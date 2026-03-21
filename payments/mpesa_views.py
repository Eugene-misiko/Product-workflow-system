import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404
from payments.models import (
    Invoice, MpesaRequest, MpesaResponse,
    Payment, Receipt
)
from payments.serializers import (
    MpesaRequestSerializer, MpesaResponseSerializer
)
from payments.mpesa_utils import initialize_stk_push
from notifications.models import Notification

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stk_push(request):
    """
    Initiate M-Pesa STK Push payment.
    This view initiates an M-Pesa STK Push request, prompting the
    customer to enter their PIN on their phone to complete payment.
    
    The payment amount is automatically determined:
    - If invoice is pending: Charge deposit amount (70%)
    - If deposit is paid: Charge remaining balance (30%)

    """
    invoice_id = request.data.get('invoice_id')
    phone_number = request.data.get('phone_number')
    
    # Validate inputs
    if not invoice_id or not phone_number:
        return Response({
            'error': 'invoice_id and phone_number are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate phone number format
    if not phone_number.startswith('254') or len(phone_number) != 12:
        return Response({
            'error': 'Invalid phone number format. Use 2547XXXXXXXX'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get invoice
    try:
        invoice = Invoice.objects.get(
            id=invoice_id,
            company=request.user.company
        )
    except Invoice.DoesNotExist:
        return Response({
            'error': 'Invoice not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check if invoice is already paid
    if invoice.status == Invoice.STATUS_PAID:
        return Response({
            'error': 'Invoice is already fully paid'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    order = invoice.order
    user = request.user

  # Determine amount to charge
    if invoice.status == Invoice.STATUS_PENDING:
        # Charge deposit (70%)
        amount = invoice.deposit_amount
        payment_type = Payment.PAYMENT_TYPE_DEPOSIT
    elif invoice.status == Invoice.STATUS_PARTIAL:
        # Charge balance (30%)
        amount = invoice.balance_due
        payment_type = Payment.PAYMENT_TYPE_BALANCE
    else:
        amount = invoice.balance_due
        payment_type = Payment.PAYMENT_TYPE_BALANCE
    
    # Create M-Pesa request
    mpesa_request = MpesaRequest.objects.create(
        user=user,
        order=order,
        invoice=invoice,
        phone_number=phone_number,
        amount=amount,
        account_reference=f"Order-{order.order_number}",
        transaction_desc=f"PrintFlow Payment - {order.order_number}"
    )
    
    # Initialize STK Push
    response_data = initialize_stk_push(mpesa_request)
    
    # Check for errors
    if 'error' in response_data or 'MerchantRequestID' not in response_data:
        return Response({
            'error': 'Failed to connect to M-Pesa',
            'details': response_data
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Save response
    mpesa_response = MpesaResponse.objects.create(
        request=mpesa_request,
        merchant_request_id=response_data.get('MerchantRequestID'),
        checkout_request_id=response_data.get('CheckoutRequestID'),
        response_code=response_data.get('ResponseCode'),
        response_description=response_data.get('ResponseDescription'),
    )
    
    logger.info(f"STK Push initiated: {mpesa_response.checkout_request_id}")
    
    return Response(
        MpesaResponseSerializer(mpesa_response).data,
        status=status.HTTP_201_CREATED
    )

@api_view(['POST'])
def mpesa_callback(request):
    """
    Handle M-Pesa payment callback.
    This endpoint receives payment confirmation from Safaricom
    after an STK Push payment is completed (or failed).
    On successful payment:
    - Updates invoice status
    - Creates payment record
    - Generates receipt
    - Sends notification to user
    """
    data = request.data
    stk_callback = data.get('Body', {}).get('stkCallback', {})
    
    merchant_request_id = stk_callback.get('MerchantRequestID')
    checkout_request_id = stk_callback.get('CheckoutRequestID')
    result_code = stk_callback.get('ResultCode')
    result_desc = stk_callback.get('ResultDesc')
    
    logger.info(f"M-Pesa Callback: CheckoutRequestID={checkout_request_id}, ResultCode={result_code}")
    
    try:
        mpesa_response = MpesaResponse.objects.get(
            merchant_request_id=merchant_request_id,
            checkout_request_id=checkout_request_id
        )
    except MpesaResponse.DoesNotExist:
        logger.error(f"MpesaResponse not found: {checkout_request_id}")
        return Response(
            {'ResultCode': 1, 'ResultDesc': 'Request not found'},
            status=status.HTTP_200_OK
        )
    # Update response
    mpesa_response.response_code = str(result_code)
    mpesa_response.response_description = result_desc
    
    if result_code == 0:
        # Payment successful
        mpesa_response.is_successful = True
        
        invoice = mpesa_response.request.invoice
        order = mpesa_response.request.order
        user = mpesa_response.request.user
        amount = mpesa_response.request.amount
        
        # Extract metadata
        metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
        
        mpesa_code = None
        amount_paid = None
        transaction_date = None
        
        for item in metadata:
            name = item.get('Name')
            value = item.get('Value')
            
            if name == 'MpesaReceiptNumber':
                mpesa_code = value
                mpesa_response.receipt_number = value
            elif name == 'Amount':
                amount_paid = value
                mpesa_response.amount_paid = value
            elif name == 'TransactionDate':
                transaction_date = str(value)
                mpesa_response.transaction_date = transaction_date
        
        mpesa_response.save()
        
        # Determine payment type
        if invoice.status == Invoice.STATUS_PENDING:
            payment_type = Payment.PAYMENT_TYPE_DEPOSIT
            invoice.status = Invoice.STATUS_PARTIAL
        else:
            payment_type = Payment.PAYMENT_TYPE_BALANCE
            invoice.status = Invoice.STATUS_PAID
        
        invoice.save()
        
        # Create payment record
        payment = Payment.objects.create(
            company=invoice.company,
            invoice=invoice,
            amount=amount_paid or amount,
            payment_type=payment_type,
            payment_method=Payment.METHOD_MPESA,
            status=Payment.STATUS_COMPLETED,
            mpesa_response=mpesa_response,
            transaction_id=mpesa_code
        )
        payment.completed_at = timezone.now()
        payment.save()
        
        # Create receipt
        receipt = Receipt.objects.create(
            company=invoice.company,
            user=user,
            order=order,
            invoice=invoice,
            payment=payment,
            mpesa_receipt=mpesa_code,
            amount_paid=amount_paid or amount,
            payment_type=payment_type
        )
        
        # Send notification
        Notification.objects.create(
            company=invoice.company,
            user=user,
            notification_type=Notification.TYPE_PAYMENT,
            title='Payment Successful',
            message=f'Your payment of ${amount_paid or amount} for order {order.order_number} was successful. Receipt: {mpesa_code}',
            related_object_type='order',
            related_object_id=order.id
        )
        
        logger.info(f"Payment successful: {mpesa_code}")
        
    else:
        # Payment failed
        mpesa_response.is_successful = False
        mpesa_response.save()
        
        logger.warning(f"Payment failed: {result_desc}")
        
        # Notify user of failure
        Notification.objects.create(
            company=mpesa_response.request.invoice.company,
            user=mpesa_response.request.user,
            notification_type=Notification.TYPE_PAYMENT,
            title='Payment Failed',
            message=f'Your payment for order {mpesa_response.request.order.order_number} failed. Reason: {result_desc}',
            related_object_type='order',
            related_object_id=mpesa_response.request.order.id
        )
    
    return Response(
        {'ResultCode': 0, 'ResultDesc': 'Success'},
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_status(request, checkout_request_id):
    """
    Check status of an M-Pesa payment.
    Use this endpoint to check if a payment was completed
    if the callback was not received or to poll for status.
    """
    try:
        mpesa_response = MpesaResponse.objects.get(
            checkout_request_id=checkout_request_id,
            request__user=request.user
        )
    except MpesaResponse.DoesNotExist:
        return Response({
            'error': 'Payment request not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    return Response({
        'checkout_request_id': mpesa_response.checkout_request_id,
        'is_successful': mpesa_response.is_successful,
        'response_code': mpesa_response.response_code,
        'response_description': mpesa_response.response_description,
        'amount_paid': mpesa_response.amount_paid,
        'receipt_number': mpesa_response.receipt_number,
        'created_at': mpesa_response.created_at
    })




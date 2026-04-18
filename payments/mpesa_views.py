import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404
from companies.models import Company
from payments.models import Invoice, MpesaRequest, MpesaResponse, Payment, Receipt
from payments.serializers import MpesaRequestSerializer, MpesaResponseSerializer, StkPushSerializer
from payments.mpesa_utils import initialize_stk_push
from notifications.models import Notification
from django.db import transaction
logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stk_push(request):
    """
    Initiate an M-Pesa STK Push payment.

    This endpoint triggers an STK Push to the customer's phone.
    The payment amount is automatically determined:
        - If invoice is pending: charge 70% deposit
        - If deposit already paid: charge remaining balance (30%)

    Request data:
        - invoice_id: ID of the invoice
        - phone_number: Customer's phone in format 2547XXXXXXXX

    Returns:
        - MpesaResponseSerializer data on success
        - Error message if validation fails or STK Push fails
    """
    serializer = StkPushSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)

    invoice = get_object_or_404(
        Invoice,
        id=serializer.validated_data['invoice_id'],
        company=request.user.company
    )

    if invoice.status == Invoice.STATUS_PAID:
        return Response({'error': 'Invoice is already fully paid.'}, status=status.HTTP_400_BAD_REQUEST)

    # Determine amount to charge
    if invoice.status == Invoice.STATUS_PENDING:
        amount = invoice.deposit_amount
        payment_type = Payment.PAYMENT_TYPE_DEPOSIT
    else:
        amount = invoice.balance_due
        payment_type = Payment.PAYMENT_TYPE_BALANCE

    # Create M-Pesa request
    mpesa_request = MpesaRequest.objects.create(
        user=request.user,
        company=invoice.company, 
        order=invoice.order,
        invoice=invoice,
        phone_number=serializer.validated_data['phone_number'],
        amount=amount,
        account_reference=f"Order-{invoice.order.order_number}",
        transaction_desc=f"PrintFlow Payment - {invoice.order.order_number}"
    )

    # Initialize STK Push
    response_data = initialize_stk_push(mpesa_request, request.user.company)

    if 'error' in response_data or 'MerchantRequestID' not in response_data:
        return Response({
            'error': 'Failed to connect to M-Pesa',
            'details': response_data
        }, status=status.HTTP_400_BAD_REQUEST)

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

ALLOWED_IPS = ["196.201.214.200", "196.201.214.206"]  
@api_view(['POST'])
def mpesa_callback(request):
    """
    Handle M-Pesa payment callback.

    This endpoint receives payment confirmation from Safaricom
    after an STK Push payment is completed (or failed).

    On successful payment:
        - Updates invoice amounts and status
        - Creates a Payment record
        - Generates a Receipt
        - Sends a Notification to the user

    On failure:
        - Updates MpesaResponse as failed
        - Sends failure Notification

    Notes:
        - Multitenancy enforced via MpesaResponse -> Invoice -> Company
        - Uses Invoice.save() to auto-update status based on amount_paid
    """
    company_id = request.GET.get("company_id")
    ip = request.META.get('REMOTE_ADDR')
    if ip not in ALLOWED_IPS:
        return Response({"error": "Unauthorized"}, status=403)
    data = request.data
    stk_callback = data.get('Body', {}).get('stkCallback', {})

    merchant_request_id = stk_callback.get('MerchantRequestID')
    checkout_request_id = stk_callback.get('CheckoutRequestID')
    result_code = stk_callback.get('ResultCode')
    result_desc = stk_callback.get('ResultDesc')

    logger.info(f"M-Pesa Callback received: CheckoutRequestID={checkout_request_id}, ResultCode={result_code}")

    try:
        mpesa_response = MpesaResponse.objects.get(
            merchant_request_id=merchant_request_id,
            checkout_request_id=checkout_request_id
        )
    except MpesaResponse.DoesNotExist:
        logger.error(f"MpesaResponse not found for CheckoutRequestID={checkout_request_id}")
        return Response({'ResultCode': 1, 'ResultDesc': 'Request not found'}, status=status.HTTP_200_OK)

    mpesa_response.response_code = str(result_code)
    mpesa_response.response_description = result_desc

    invoice = mpesa_response.request.invoice
    order = mpesa_response.request.order
    user = mpesa_response.request.user

    if result_code == 0:
        # Payment successful
        mpesa_response.is_successful = True

        # Extract metadata
        metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
        mpesa_code = None
        amount_paid = None
        transaction_date = None
        for item in metadata:
            if item.get('Name') == 'MpesaReceiptNumber':
                mpesa_code = item.get('Value')
                mpesa_response.receipt_number = mpesa_code
            elif item.get('Name') == 'Amount':
                amount_paid = item.get('Value')
                mpesa_response.amount_paid = amount_paid
            elif item.get('Name') == 'TransactionDate':
                transaction_date = str(item.get('Value'))
                mpesa_response.transaction_date = transaction_date
        mpesa_response.save()

        # Update invoice amounts
    paid = amount_paid or mpesa_response.request.amount

    with transaction.atomic():
        if not Payment.objects.filter(mpesa_response=mpesa_response).exists():
            invoice.amount_paid += paid

            if invoice.amount_paid >= invoice.deposit_amount:
                invoice.deposit_paid = invoice.deposit_amount

            invoice.balance_due = invoice.total_amount - invoice.amount_paid
            #invoice.save()

            payment_type = (
                Payment.PAYMENT_TYPE_DEPOSIT
                if mpesa_response.request.amount == invoice.deposit_amount
                else Payment.PAYMENT_TYPE_BALANCE
            )

            # payment = Payment.objects.create(
            #     company=invoice.company,
            #     invoice=invoice,
            #     amount=paid,
            #     payment_method=Payment.METHOD_MPESA,
            #     payment_type=payment_type,
            #     status=Payment.STATUS_COMPLETED,
            #     mpesa_response=mpesa_response,
            #     transaction_id=mpesa_code,
            #     completed_at=timezone.now()
            # )

            # Receipt.objects.create(
            #     company=invoice.company,
            #     user=user,
            #     order=order,
            #     invoice=invoice,
            #     payment=payment,
            #     mpesa_receipt=mpesa_code,
            #     amount_paid=paid,
            #     payment_type=payment.payment_type
            # )

        # Send Notification
        Notification.objects.create(
            company=invoice.company,
            user=user,
            notification_type=Notification.TYPE_PAYMENT,
            title='Payment Successful',
            message=f'Your payment of {amount_paid or mpesa_response.request.amount} for order {order.order_number} was successful. Receipt: {mpesa_code}',
            related_object_type='order',
            related_object_id=order.id
        )

        logger.info(f"Payment successful: {mpesa_code}")

    else:
        # Payment failed
        mpesa_response.is_successful = False
        mpesa_response.save()

        Notification.objects.create(
            company=mpesa_response.request.invoice.company,
            user=mpesa_response.request.user,
            notification_type=Notification.TYPE_PAYMENT,
            title='Payment Failed',
            message=f'Your payment for order {order.order_number} failed. Reason: {result_desc}',
            related_object_type='order',
            related_object_id=order.id
        )

        logger.warning(f"Payment failed: {result_desc}")

    return Response({'ResultCode': 0, 'ResultDesc': 'Success'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_status(request, checkout_request_id):
    """
    Check the status of an M-Pesa payment.

    This endpoint allows users to verify if a payment was completed.
    It is useful if the callback was not received or for polling payment status.

    Args:
        checkout_request_id (str): The M-Pesa CheckoutRequestID

    Returns:
        JSON response with:
            - checkout_request_id
            - is_successful
            - response_code
            - response_description
            - amount_paid
            - receipt_number
            - created_at
    """
    try:
        mpesa_response = MpesaResponse.objects.get(
            checkout_request_id=checkout_request_id,
            request__invoice__company=request.user.company
        )
    except MpesaResponse.DoesNotExist:
        return Response({'error': 'Payment request not found'}, status=404)

    return Response({
        'checkout_request_id': mpesa_response.checkout_request_id,
        'is_successful': mpesa_response.is_successful,
        'response_code': mpesa_response.response_code,
        'response_description': mpesa_response.response_description,
        'amount_paid': mpesa_response.amount_paid,
        'receipt_number': mpesa_response.receipt_number,
        'created_at': mpesa_response.created_at
    })
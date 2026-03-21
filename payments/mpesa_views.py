import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
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

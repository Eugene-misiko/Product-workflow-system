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
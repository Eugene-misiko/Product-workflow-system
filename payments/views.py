from rest_framework import status, generics, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.http import HttpResponse
from django.db.models import Sum
from rest_framework.decorators import api_view, permission_classes
import logging
from django.http import HttpResponseForbidden
from .models import Invoice, Payment, Receipt, MpesaRequest, MpesaResponse
from .serializers import (
    InvoiceSerializer, PaymentSerializer, CreatePaymentSerializer, 
    ReceiptSerializer, StkPushSerializer
)
from .mpesa_utils import initialize_stk_push
from .pdf_utils import generate_invoice_pdf, generate_receipt_pdf
from notifications.models import Notification

logger = logging.getLogger(__name__)

# ----------------------------
# Invoice ViewSet
# ----------------------------
class InvoiceViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Invoice.objects.filter(company=user.company)

        if user.role == 'client':
            queryset = queryset.filter(order__user=user)

        return queryset.order_by('-created_at')


# ----------------------------
# Download Invoice PDF
# ----------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_invoice(request, pk):
    invoice = get_object_or_404(
        Invoice,
        pk=pk,
        company=request.user.company
    )

    if request.user.role != 'admin' and invoice.order.user != request.user:
        return HttpResponse('Unauthorized', status=401)

    return generate_invoice_pdf(invoice)


# ----------------------------
# Send Invoice (Email)
# ----------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_invoice(request, pk):
    """Send invoice to client via email."""
    invoice = get_object_or_404(
        Invoice,
        pk=pk,
        company=request.user.company
    )

    if request.user.role != 'admin':
        return Response({'error': 'Only admin can send invoice'}, status=403)

    return Response({'message': 'Invoice sent.'})


# ----------------------------
# Pending Deposit Invoices
# ----------------------------
class PendingDepositInvoicesView(generics.ListAPIView):
    """List invoices that are pending deposit payment."""
    permission_classes = [IsAuthenticated]
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        return Invoice.objects.filter(
            company=self.request.user.company,
            status='pending'
        ).order_by('-created_at')


# ----------------------------
# Pending Balance Invoices
# ----------------------------
class PendingBalanceInvoicesView(generics.ListAPIView):
    """List invoices that have paid deposit but still have balance due."""
    permission_classes = [IsAuthenticated]
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        return Invoice.objects.filter(
            company=self.request.user.company,
            status='partial'
        ).order_by('-created_at')


# ----------------------------
# Payment ViewSet (Read-only)
# ----------------------------
class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """Payments for invoices."""
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Payment.objects.filter(company=user.company)

        if user.role == 'client':
            queryset = queryset.filter(invoice__order__user=user)

        return queryset.order_by('-created_at')


# ----------------------------
# Receipt ViewSet (Read-only)
# ----------------------------
class ReceiptViewSet(viewsets.ReadOnlyModelViewSet):
    """Receipts for completed payments."""
    permission_classes = [IsAuthenticated]
    serializer_class = ReceiptSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Receipt.objects.filter(company=user.company)

        if user.role == 'client':
            queryset = queryset.filter(user=user)

        return queryset.order_by('-created_at')


# ----------------------------
# Download Receipt PDF
# ----------------------------
def download_receipt(request, pk):
    """Download receipt PDF."""
    receipt = get_object_or_404(Receipt, pk=pk, company=request.user.company)

    if request.user.role != 'admin' and receipt.user != request.user:
        return HttpResponseForbidden('Unauthorized')

    return generate_receipt_pdf(receipt)


# ----------------------------
# Record Manual Payment (Admin only)
# ----------------------------
class RecordPaymentView(APIView):
    """Manually record a payment for an invoice (Admin only)."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_company_admin:
            return Response({'error': 'Only admin can record payments.'}, status=403)

        serializer = CreatePaymentSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
       
        invoice = get_object_or_404(
            Invoice,
            id=serializer.validated_data['invoice_id'],
            company=request.user.company
        )
        amount = serializer.validated_data['amount']
        payment_type = serializer.validated_data['payment_type']
        # prevent overpayment
        if amount > invoice.balance_due:
            return Response({'error': 'Payment amount exceeds remaining balance.'}, status=400)

        # prevent paying balance before deposit
        if payment_type == 'balance' and not invoice.is_deposit_paid:
            return Response(
                {"error": "Deposit must be paid before balance"},
                status=400
            )
        payment = Payment.objects.create(
            company=invoice.company,
            invoice=invoice,
            amount=serializer.validated_data['amount'],
            payment_type=serializer.validated_data['payment_type'],
            payment_method=serializer.validated_data['payment_method'],
            transaction_id=serializer.validated_data.get('transaction_id', ''),
            notes=serializer.validated_data.get('notes', ''),
            status='completed',
            recorded_by=request.user,
            completed_at=timezone.now()
        )
        mpesa_receipt =payment.transaction_id if payment.payment_method == 'mpesa' else ''

        # Update invoice payment info
        invoice.amount_paid += payment.amount

        if payment.payment_type == 'deposit':
            invoice.deposit_paid += payment.amount
        # This will trigger the save() method to recalculate amounts and update status  
        invoice.save()   

        # Create receipt
        receipt = Receipt.objects.create(
            company=invoice.company,
            user=invoice.order.user,
            order=invoice.order,
            invoice=invoice,
            payment=payment,
            mpesa_receipt=mpesa_receipt,
            amount_paid=payment.amount,
            payment_type=payment.payment_type
        )

        # Notify client
        Notification.objects.create(
            company=invoice.company,
            user=invoice.order.user,
            notification_type='payment',
            title='Payment Received',
            message=f'Payment of KSh {payment.amount} received for order {invoice.order.order_number}',
            related_object_type='invoice',
            related_object_id=invoice.id
        )

        return Response({
            'payment': PaymentSerializer(payment).data,
            'receipt': ReceiptSerializer(receipt).data
        }, status=201)


# ----------------------------
# Payment Stats
# ----------------------------
class PaymentStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = request.user.company

        total_revenue = Payment.objects.filter(
            company=company,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0

        pending_invoices = Invoice.objects.filter(
            company=company,
            status__in=['pending', 'partial']
        ).count()

        return Response({
            'total_revenue': str(total_revenue),
            'pending_invoices': pending_invoices
        })
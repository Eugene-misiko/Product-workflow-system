"""
Invoice, Payment, and Receipt views for the PrintFlow application.

Covers:
  - Invoice CRUD (InvoiceViewSet)
  - Invoice PDF download and email delivery
  - Pending deposit / pending balance list views
  - Payment list and manual recording (admin only)
  - Receipt list and PDF download
  - Payment statistics dashboard data
"""
import logging
from rest_framework import status, generics, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.http import HttpResponse, HttpResponseForbidden
from django.db.models import Sum
from django.template.loader import render_to_string
from rest_framework.decorators import api_view, permission_classes
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.db import transaction

from .models import Invoice, Payment, Receipt, MpesaRequest, MpesaResponse
from .serializers import (
    InvoiceSerializer,
    PaymentSerializer,
    CreatePaymentSerializer,
    ReceiptSerializer,
    StkPushSerializer,
)
from .mpesa_utils import initialize_stk_push
from .pdf_utils import generate_invoice_pdf, generate_receipt_pdf
from notifications.models import Notification

logger = logging.getLogger(__name__)

# Invoice ViewSet
class InvoiceViewSet(viewsets.ModelViewSet):
    """
    CRUD endpoints for invoices, scoped to the authenticated user's company.

    Clients only see invoices belonging to their own orders.
    Admins/staff see all invoices for the company.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Invoice.objects.filter(company=user.company)
        if user.role == "client":
            queryset = queryset.filter(order__user=user)
        return queryset.order_by("-created_at")

# Download Invoice PDF

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_invoice(request, pk):
    """
    Stream an invoice as a PDF file.

    Clients can only download their own invoices.
    Admins can download any invoice in their company.
    """
    invoice = get_object_or_404(Invoice, pk=pk, company=request.user.company)

    if request.user.role != "admin" and invoice.order.user != request.user:
        return HttpResponse("Unauthorized", status=401)

    return generate_invoice_pdf(invoice)

# Send Invoice via Email
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_invoice(request, pk):
    """
    Send an invoice PDF + payment link to the client's email address.

    Admin only. Generates an HTML email with the invoice PDF attached and
    a deep-link back to the payments page pre-filled with this invoice.
    """
    invoice = get_object_or_404(Invoice, pk=pk, company=request.user.company)

    if request.user.role != "admin":
        return Response({"error": "Only admin can send invoices."}, status=403)

    client = invoice.order.user
    if not client.email:
        return Response({"error": "Client has no email address on file."}, status=400)

    payment_url = f"{settings.FRONTEND_URL}/payments?invoice={invoice.id}"

    html_content = render_to_string(
        "emails/invoice.html",
        {
            "name": client.get_full_name() or client.username,
            "invoice_number": invoice.invoice_number,
            "amount": invoice.total_amount,
            "payment_url": payment_url,
        },
    )

    email = EmailMultiAlternatives(
        subject=f"Invoice {invoice.invoice_number} — PrintFlow",
        body="Please view this invoice in an HTML-capable email client.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[client.email],
    )
    email.attach_alternative(html_content, "text/html")

    pdf_response = generate_invoice_pdf(invoice)
    email.attach(
        f"Invoice_{invoice.invoice_number}.pdf",
        pdf_response.content,
        "application/pdf",
    )
    email.send()

    logger.info("Invoice %s emailed to %s", invoice.invoice_number, client.email)
    return Response({"message": "Invoice sent with PDF and payment link."})


# Pending Deposit Invoices
class PendingDepositInvoicesView(generics.ListAPIView):
    """
    List invoices that are waiting for the initial 70% deposit payment.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        return Invoice.objects.filter(
            company=self.request.user.company,
            status=Invoice.STATUS_PENDING,
        ).order_by("-created_at")


# Pending Balance Invoices
class PendingBalanceInvoicesView(generics.ListAPIView):
    """
    List invoices where the deposit has been paid but the 30% balance is due.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        return Invoice.objects.filter(
            company=self.request.user.company,
            status="partial",
        ).order_by("-created_at")


# Payment ViewSet (read-only)
class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only list/detail for payments.

    Clients see only payments linked to their own orders.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Payment.objects.filter(company=user.company)
        if user.role == "client":
            queryset = queryset.filter(invoice__order__user=user)
        return queryset.order_by("-created_at")



# Receipt ViewSet (read-only)

class ReceiptViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only list/detail for receipts.

    Clients see only their own receipts.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = ReceiptSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Receipt.objects.filter(company=user.company)
        if user.role == "client":
            queryset = queryset.filter(user=user)
        return queryset.order_by("-created_at")

# Download Receipt PDF

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_receipt(request, pk):
    """
    Stream a receipt as a PDF file.

    Clients can only download their own receipts.
    """
    receipt = get_object_or_404(Receipt, pk=pk, company=request.user.company)

    if request.user.role != "admin" and receipt.user != request.user:
        return HttpResponseForbidden("Unauthorized")

    return generate_receipt_pdf(receipt)

# Record Manual Payment (admin only)

class RecordPaymentView(APIView):
    """
    Manually record a cash, card, or M-Pesa payment for an invoice.

    Admin only. Validates that:
      - Payment amount does not exceed the remaining balance.
      - Balance payments are not recorded before the deposit is paid.

    On success:
      - Creates Payment record.
      - Creates Receipt record.
      - Updates invoice.amount_paid and recalculates invoice.status.
      - Sends an in-app Notification to the client.

    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_company_admin:
            return Response({"error": "Only admins can record payments."}, status=403)

        serializer = CreatePaymentSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        invoice = get_object_or_404(
            Invoice,
            id=serializer.validated_data["invoice_id"],
            company=request.user.company,
        )

        amount = serializer.validated_data["amount"]
        payment_type = serializer.validated_data["payment_type"]

        # Business rule: prevent overpayment
        if amount > invoice.balance_due:
            return Response(
                {"error": "Payment amount exceeds the remaining balance."},
                status=400,
            )

        #  balance cannot be paid before deposit
        if payment_type == "balance" and not invoice.is_deposit_paid:
            return Response(
                {"error": "The deposit must be paid before recording a balance payment."},
                status=400,
            )

        with transaction.atomic():
            payment = Payment.objects.create(
                company=invoice.company,
                invoice=invoice,
                amount=amount,
                payment_type=payment_type,
                payment_method=serializer.validated_data["payment_method"],
                transaction_id=serializer.validated_data.get("transaction_id", ""),
                notes=serializer.validated_data.get("notes", ""),
                status=Payment.STATUS_COMPLETED,
                recorded_by=request.user,
                completed_at=timezone.now(),
            )

            mpesa_receipt = (
                payment.transaction_id
                if payment.payment_method == "mpesa"
                else ""
            )

            # Re-fetch with row lock to prevent race conditions
            invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
            invoice.amount_paid = (invoice.amount_paid or 0) + amount

            if invoice.amount_paid >= invoice.total_amount:
                invoice.status = Invoice.STATUS_PAID if hasattr(Invoice, "STATUS_PAID") else "paid"
            elif invoice.amount_paid > 0:
                invoice.status = "partial"

            invoice.save() 

            receipt = Receipt.objects.create(
                company=invoice.company,
                user=invoice.order.user,
                order=invoice.order,
                invoice=invoice,
                payment=payment,
                mpesa_receipt=mpesa_receipt,
                amount_paid=amount,
                payment_type=payment.payment_type,
            )

            Notification.objects.create(
                company=invoice.company,
                user=invoice.order.user,
                notification_type=Notification.TYPE_PAYMENT
                if hasattr(Notification, "TYPE_PAYMENT")
                else "payment",
                title="Payment Received",
                message=(
                    f"Payment of KES {amount:,.0f} received for "
                    f"order {invoice.order.order_number}."
                ),
                related_object_type="invoice",
                related_object_id=invoice.id,
            )

        logger.info(
            "Manual payment recorded: invoice=%s amount=%s by=%s",
            invoice.invoice_number,
            amount,
            request.user.username,
        )

        return Response(
            {
                "payment": PaymentSerializer(payment).data,
                "receipt": ReceiptSerializer(receipt).data,
                "invoice": InvoiceSerializer(invoice).data,
            },
            status=201,
        )

# Payment Statistics

class PaymentStatsView(APIView):
    """
    Aggregated payment statistics for the authenticated company.

    Returns total revenue (completed payments), count of pending invoices,
    and total number of completed payments.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = request.user.company

        total_revenue = (
            Payment.objects.filter(company=company, status=Payment.STATUS_COMPLETED)
            .aggregate(total=Sum("amount"))["total"]
            or 0
        )

        pending_count = Invoice.objects.filter(
            company=company,
            status__in=["pending", "partial"],
        ).count()

        total_payments = Payment.objects.filter(
            company=company,
            status=Payment.STATUS_COMPLETED,
        ).count()

        return Response(
            {
                "total_revenue": str(total_revenue),
                "pending_invoices": pending_count,
                "total_payments": total_payments,
                "pending": pending_count,  
            }
        )
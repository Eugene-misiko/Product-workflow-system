from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Order,Invoice
from .serializers import OrderSerializer
from .utils import generate_invoice_pdf
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.http import HttpResponse

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            print("ORDER VALIDATION ERROR:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer)

        return Response(serializer.data, status=status.HTTP_201_CREATED)    
    # ROLE BASED VISIBILITY
    def get_queryset(self):
        user = self.request.user

        if user.role == "admin":
            return Order.objects.all()

        # Designer sees only orders waiting for design
        if user.role == "designer":
            return Order.objects.filter(
                needs_design=True,
                status__in=["pending_design", "design_rejected"]
            )

        # Printer sees only completed designs
        if user.role == "printer":
            return Order.objects.filter(status="design_completed")

        # Client sees only their own orders
        return Order.objects.filter(user=user)

    # CLIENT CREATES ORDER
    def perform_create(self, serializer):
        order = serializer.save(user=self.request.user)

        if order.needs_design:
            order.status = "pending_design"
        else:
            order.status = "design_completed"

        order.save()

    # DESIGNER COMPLETES DESIGN
    @action(detail=True, methods=["put"])
    def design_complete(self, request, pk=None):
        if request.user.role != "designer":
            return Response({"error": "Only designer allowed"}, status=403)

        order = self.get_object()

        order.status = "design_completed"
        order.rejection_reason = ""
        order.save()

        return Response({"message": "Design completed successfully"})

    # DESIGNER REJECTS
    @action(detail=True, methods=["put"])
    def design_reject(self, request, pk=None):
        if request.user.role != "designer":
            return Response({"error": "Only designer allowed"}, status=403)

        reason = request.data.get("reason")
        if not reason:
            return Response({"error": "Rejection reason required"}, status=400)

        order = self.get_object()
        order.status = "design_rejected"
        order.rejection_reason = reason
        order.save()

        return Response({"message": "Order rejected by designer"})

    # PRINTER APPROVES
    @action(detail=True, methods=["put"])
    def approve(self, request, pk=None):
        if request.user.role != "printer":
            return Response({"error": "Only printer allowed"}, status=403)

        order = self.get_object()

        if order.status != "design_completed":
            return Response({"error": "Design not completed"}, status=400)

        order.status = "approved"
        order.save()

        return Response({"message": "Order approved for printing"})

    # PRINTER REJECTS
    @action(detail=True, methods=["put"])
    def print_reject(self, request, pk=None):
        if request.user.role != "printer":
            return Response({"error": "Only printer allowed"}, status=403)

        reason = request.data.get("reason")
        if not reason:
            return Response({"error": "Rejection reason required"}, status=400)

        order = self.get_object()
        order.status = "print_rejected"
        order.rejection_reason = reason
        order.save()

        return Response({"message": "Order rejected by printer"})
    @action(detail=True, methods=["put"])
    def mark_in_print(self, request, pk=None):
        if request.user.role != "printer":
            return Response({"error": "Only printer allowed"}, status=403)

        order = self.get_object()

        if order.status != "approved":
            return Response({"error": "Order not approved yet"}, status=400)

        order.status = "in_print"
        order.save()

        return Response({"message": "Printing started"})


    # PRINTER MARKS COMPLETED
    @action(detail=True, methods=["put"])
    def mark_completed(self, request, pk=None):
        if request.user.role != "printer":
            return Response({"error": "Only printer allowed"}, status=403)

        order = self.get_object()

        if order.status != "in_print":
            return Response({"error": "Order not in printing stage"}, status=400)

        order.status = "completed"
        order.save()

        return Response({"message": "Order completed successfully"})
    # PRINTER START PRINTING
    @action(detail=True, methods=["put"])
    def start_printing(self, request, pk=None):
        if request.user.role != "printer":
            return Response({"error": "Only printer allowed"}, status=403)

        order = self.get_object()

        if order.status != "approved":
            return Response({"error": "Order not approved yet"}, status=400)

        order.status = "printing"
        order.save()

        return Response({"message": "Printing started"})


    # PRINTER COMPLETE PRINT
    @action(detail=True, methods=["put"])
    def complete_print(self, request, pk=None):
        if request.user.role != "printer":
            return Response({"error": "Only printer allowed"}, status=403)

        order = self.get_object()

        if order.status != "printing":
            return Response({"error": "Order not printing"}, status=400)

        order.status = "completed"
        order.save()

        return Response({"message": "Printing completed"})
@api_view(["GET"])
def get_invoice(request, pk):
    try:
        invoice = Invoice.objects.select_related("order__product").get(pk=pk)

        data = {
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "product_name": invoice.order.product.name,
            "quantity": invoice.order.quantity,
            "unit_price": invoice.order.product.price,
            "total_amount": invoice.total_amount,
            "deposit_amount": invoice.deposit_amount,
            "balance_due": invoice.balance_due,
            "status": invoice.status,
        }

        return Response(data)

    except Invoice.DoesNotExist:
        return Response({"error": "Invoice not found"}, status=404)



def download_invoice(request, pk):

    invoice = Invoice.objects.select_related("order__product").get(pk=pk)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="invoice_{invoice.id}.pdf"'

    p = canvas.Canvas(response, pagesize=letter)

    y = 750

    p.setFont("Helvetica-Bold", 18)
    p.drawString(200, y, "ZENITH ZEST COMPANY INVOICE")

    y -= 40
    p.setFont("Helvetica", 12)

    p.drawString(50, y, f"Invoice Number: {invoice.invoice_number}")
    y -= 20

    p.drawString(50, y, f"Product: {invoice.order.product.name}")
    y -= 20

    p.drawString(50, y, f"Quantity: {invoice.order.quantity}")
    y -= 20

    p.drawString(50, y, f"Unit Price: {invoice.order.product.price}")
    y -= 20

    p.drawString(50, y, f"Total Amount: {invoice.total_amount}")
    y -= 20

    p.drawString(50, y, f"Deposit Required: {invoice.deposit_amount}")
    y -= 20

    p.drawString(50, y, f"Balance Due: {invoice.balance_due}")
    y -= 40

    p.drawString(50, y, f"Status: {invoice.status}")

    p.showPage()
    p.save()

    return response

    
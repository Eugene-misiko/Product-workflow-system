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
from reportlab.lib.colors import HexColor, black,grey
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime   

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

    doc = SimpleDocTemplate(
        response,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )
    styles = getSampleStyleSheet()
    elements = []
    # HEADER (LOGO + COMPANY)
    #logo = Image("media/logo.png", width=70, height=70)
    company_info = [
        Paragraph("<b>ZENITH ZEST LIMITED</b>", styles["Title"]),
        Paragraph("P.O Box 10257-00400, Nairobi Kenya", styles["Normal"]),
        Paragraph("Tel: 0707 458 198, 0700 300 051", styles["Normal"]),
        Paragraph("Email: info@zenithzest.com", styles["Normal"]),
        Paragraph("Website: www.zenithzest.com", styles["Normal"]),
    ]
    header = Table([[ company_info]])#removed logo
    header.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP")
    ]))
    elements.append(header)
    elements.append(Spacer(1,10))
    # ORANGE LINE
    line = Table([[""]], colWidths=[520], rowHeights=[4])
    line.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),HexColor("#f97316"))
    ]))
    elements.append(line)
    elements.append(Spacer(1,20))
    # INVOICE INFO
    invoice_info = [
        ["", Paragraph("<b>INVOICE</b>", styles["Heading2"])],
        ["", f"Invoice No: {invoice.invoice_number}"],
        ["", f"Date: {datetime.today().strftime('%d %B %Y')}"]
    ]

    info_table = Table(invoice_info, colWidths=[350,170])
    elements.append(info_table)
    elements.append(Spacer(1,20))

    # CUSTOMER
    elements.append(Paragraph("<b>TO: AM SOLUTIONS</b>", styles["Normal"]))
    elements.append(Spacer(1,20))
    # PRODUCTS TABLE
    product = invoice.order.product
    items = [
        ["Description", "Quantity", "Price (Ksh)", "Amount (Ksh)"],
        [
            product.name,
            invoice.order.quantity,
            product.price,
            invoice.total_amount
        ],
    ]
    item_table = Table(items, colWidths=[260,80,90,90])
    item_table.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),0.5,HexColor("#999999")),
        ("BACKGROUND",(0,0),(-1,0),HexColor("#eeeeee")),
        ("ALIGN",(1,1),(-1,-1),"CENTER")
    ]))
    elements.append(item_table)
    elements.append(Spacer(1,25))
    # TOTALS BOX
    totals = [
        ["Sub-Total", invoice.total_amount],
        ["VAT", "0"],
        ["Total", invoice.total_amount]
    ]
    totals_table = Table(totals, colWidths=[120,100])
    totals_table.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),0.7,HexColor("#999999")),
        ("ALIGN",(1,0),(-1,-1),"RIGHT"),
        ("FONTNAME",(0,2),(-1,2),"Helvetica-Bold")
    ]))
    totals_wrapper = Table([[ "", totals_table ]], colWidths=[320,200])
    elements.append(totals_wrapper)
    elements.append(Spacer(1,40))
    # PAYMENT DETAILS
    elements.append(Paragraph("<b>Payment Details</b>", styles["Normal"]))
    elements.append(Paragraph("COOPERATIVE BANK - MOI AVENUE BRANCH", styles["Normal"]))
    elements.append(Paragraph("ZENITH ZEST LIMITED", styles["Normal"]))
    elements.append(Paragraph("ACCOUNT NO: 011924368500", styles["Normal"]))
    elements.append(Paragraph("PIN: P052013652J", styles["Normal"]))
    elements.append(Paragraph("TEL: 0707458198", styles["Normal"]))
    elements.append(Spacer(1,40))
    # FOOTER LINE
    footer_line = Table([[""]], colWidths=[520], rowHeights=[5])
    footer_line.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),HexColor("#f97316"))
    ]))
    elements.append(footer_line)
    elements.append(Spacer(1,10))
    footer_text = "Printing • Branding • Stationery • Office Equipments • Customized Notebooks"
    elements.append(Paragraph(footer_text, styles["Normal"]))
    doc.build(elements)

    return response

    
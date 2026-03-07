from reportlab.pdfgen import canvas
from django.http import HttpResponse

def generate_invoice_pdf(invoice):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="invoice_{invoice.id}.pdf"'
    p = canvas.Canvas(response)
    p.setFont("Helvetica-Bold", 18)
    p.drawString(200, 800, "ZENITH ZEST LIMITED")
    p.setFont("Helvetica", 12)
    p.drawString(50, 760, f"Invoice No: {invoice.invoice_number}")
    p.drawString(50, 740, f"Client: {invoice.user.username}")
    p.drawString(50, 700, f"Product: {invoice.order.product.name}")
    p.drawString(50, 680, f"Quantity: {invoice.order.quantity}")
    p.drawString(50, 640, f"Total Amount: {invoice.total_amount} Ksh")
    p.drawString(50, 620, f"Deposit Required: {invoice.deposit_amount} Ksh")
    p.showPage()
    p.save()

    return response
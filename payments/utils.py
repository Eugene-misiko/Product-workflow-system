from reportlab.pdfgen import canvas
from django.http import HttpResponse

def generate_receipt_pdf(receipt):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="receipt_{receipt.id}.pdf"'
    p = canvas.Canvas(response)
    p.setFont("Helvetica-Bold", 18)
    p.drawString(200, 800, "ZENITH ZEST LIMITED")
    p.setFont("Helvetica", 12)
    p.drawString(50, 760, f"Receipt No: {receipt.receipt_number}")
    p.drawString(50, 740, f"Client: {receipt.user.username}")
    p.drawString(50, 700, f"Order ID: {receipt.order.id}")
    p.drawString(50, 660, f"Amount Paid: {receipt.amount_paid} Ksh")
    p.drawString(50, 640, f"M-Pesa Code: {receipt.mpesa_receipt}")
    p.showPage()
    p.save()

    return response
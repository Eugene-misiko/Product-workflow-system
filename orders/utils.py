from reportlab.pdfgen import canvas
from django.http import HttpResponse

def generate_invoice_pdf(invoice):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'
    p = canvas.Canvas(response)
    p.drawString(100, 800, f"Invoice Number: {invoice.invoice_number}")
    p.drawString(100, 780, f"Total Amount: {invoice.total_amount}")
    p.drawString(100, 760, f"Deposit (70%): {invoice.deposit_amount}")
    p.drawString(100, 740, f"Balance Due: {invoice.balance_due}")
    y = 700
    for item in invoice.order.items.all():
        p.drawString(
            100,
            y,
            f"{item.product_name} - Qty: {item.quantity} - Total: {item.total_price}")
        y -= 20
    p.showPage()
    p.save()

    return response
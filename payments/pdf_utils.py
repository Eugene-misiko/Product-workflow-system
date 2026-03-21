"""
PDF Generation Utilities.
This module provides functions for generating PDF invoices
and receipts for the PrintFlow system.
"""
import os
from io import BytesIO
from django.conf import settings
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import logging

logger = logging.getLogger(__name__)


def generate_invoice_pdf(invoice):
    """
    Generate a PDF invoice with
    - Company branding
    - Invoice details
    - Order items
    - Payment information
    - Deposit amount (70%)
    - Balance due
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a365d'),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2d3748'),
        spaceAfter=10
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#4a5568')
    )
    
    # Build content
    content = []
    
    # Header
    company = invoice.company
    
    # Company name and logo
    content.append(Paragraph(company.name, title_style))
    content.append(Paragraph(company.address, normal_style))
    content.append(Paragraph(f"{company.city}, {company.country}", normal_style))
    content.append(Paragraph(f"Email: {company.email} | Phone: {company.phone}", normal_style))
    content.append(Spacer(1, 30))
    
    # Invoice Title
    content.append(Paragraph("INVOICE", title_style))
    content.append(Spacer(1, 20))
    
    # Invoice Details
    invoice_data = [
        ['Invoice Number:', invoice.invoice_number],
        ['Invoice Date:', invoice.issue_date.strftime('%B %d, %Y')],
        ['Due Date:', invoice.due_date.strftime('%B %d, %Y') if invoice.due_date else 'Upon Receipt'],
        ['Status:', invoice.get_status_display()],
    ]
    
    invoice_table = Table(invoice_data, colWidths=[3*cm, 6*cm])
    invoice_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#4a5568')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    content.append(invoice_table)
    content.append(Spacer(1, 30))
    
    # Client Details
    content.append(Paragraph("Bill To:", heading_style))
    client = invoice.order.user
    content.append(Paragraph(f"<b>{client.get_full_name()}</b>", normal_style))
    content.append(Paragraph(client.email, normal_style))
    if client.phone:
        content.append(Paragraph(client.phone, normal_style))
    content.append(Spacer(1, 30))
    
    # Order Items
    content.append(Paragraph("Order Details:", heading_style))
    
    items_data = [['Description', 'Quantity', 'Unit Price', 'Amount']]
    
    for item in invoice.order.items.all():
        items_data.append([
            item.product.name,
            str(item.quantity),
            f"${item.unit_price:.2f}",
            f"${item.subtotal:.2f}"
        ])
    
    items_table = Table(items_data, colWidths=[8*cm, 2.5*cm, 3*cm, 3*cm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
    ]))
    content.append(items_table)
    content.append(Spacer(1, 20))
    
    # Totals
    totals_data = [
        ['Subtotal:', f"Ksh{invoice.subtotal:.2f}"],
        ['Tax:', f"Ksh{invoice.tax:.2f}"],
        ['Delivery Fee:', f"Ksh{invoice.delivery_fee:.2f}"],
        ['Discount:', f"-Ksh{invoice.discount:.2f}"],
        ['', ''],
        ['Total Amount:', f"Ksh{invoice.total_amount:.2f}"],
        ['', ''],
        [f'Deposit Required ({invoice.deposit_percentage}%):', f"${invoice.deposit_amount:.2f}"],
        ['Deposit Paid:', f"Ksh{invoice.deposit_paid:.2f}"],
        ['Balance Due:', f"Ksh{invoice.balance_due:.2f}"],
    ]
    
    totals_table = Table(totals_data, colWidths=[10*cm, 6.5*cm])
    totals_table.setStyle(TableStyle([
        ('FONTNAME', (0, 5), (-1, 5), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 5), (-1, 5), 12),
        ('TEXTCOLOR', (0, 5), (-1, 5), colors.HexColor('#1a365d')),
        ('FONTNAME', (0, 7), (-1, 7), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 7), (-1, 7), colors.HexColor('#c53030')),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    content.append(totals_table)
    content.append(Spacer(1, 30))
    
    # Payment Instructions
    content.append(Paragraph("Payment Instructions:", heading_style))
    content.append(Paragraph(
        f"A deposit of {invoice.deposit_percentage}% (${invoice.deposit_amount:.2f}) is required before work can begin. "
        "Payment can be made via M-Pesa or bank transfer.",
        normal_style
    ))
    content.append(Spacer(1, 20))
    
    # Terms
    content.append(Paragraph("Terms & Conditions:", heading_style))
    content.append(Paragraph(invoice.terms, normal_style))
    
    # Build PDF
    doc.build(content)
    
    # Get PDF content
    pdf = buffer.getvalue()
    buffer.close()
    
    # Create response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'
    
    return response


def generate_receipt_pdf(receipt):
    """
    Generate a PDF receipt with
    - Company branding
    - Receipt details
    - Payment information
    - M-Pesa transaction details (if applicable)
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a365d'),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2d3748'),
        spaceAfter=10
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#4a5568')
    )
    success_style = ParagraphStyle(
        'Success',
        parent=styles['Normal'],
        fontSize=16,
        textColor=colors.HexColor('#38a169'),
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Build content
    content = []
    
    # Header
    company = receipt.company
    
    content.append(Paragraph(company.name, title_style))
    content.append(Paragraph(company.address, normal_style))
    content.append(Paragraph(f"{company.city}, {company.country}", normal_style))
    content.append(Spacer(1, 30))
    # Receipt Title
    content.append(Paragraph("PAYMENT RECEIPT", title_style))
    content.append(Spacer(1, 10))
    # Success Badge
    content.append(Paragraph("✓ PAYMENT SUCCESSFUL", success_style))
    content.append(Spacer(1, 30))
    # Receipt Details
    receipt_data = [
        ['Receipt Number:', f"RCP-{str(receipt.receipt_number)[:8].upper()}"],
        ['Date:', receipt.created_at.strftime('%B %d, %Y at %I:%M %p')],
        ['Payment Type:', receipt.get_payment_type_display()],
    ]
    if receipt.mpesa_receipt:
        receipt_data.append(['M-Pesa Receipt:', receipt.mpesa_receipt])
    
    receipt_table = Table(receipt_data, colWidths=[4*cm, 10*cm])
    receipt_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#4a5568')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    content.append(receipt_table)
    content.append(Spacer(1, 30))
    
    # Client Details
    content.append(Paragraph("Received From:", heading_style))
    content.append(Paragraph(f"<b>{receipt.user.get_full_name()}</b>", normal_style))
    content.append(Paragraph(receipt.user.email, normal_style))
    if receipt.user.phone:
        content.append(Paragraph(receipt.user.phone, normal_style))
    content.append(Spacer(1, 30))
    
    # Order Details
    content.append(Paragraph("Order Details:", heading_style))
    content.append(Paragraph(f"Order Number: <b>{receipt.order.order_number}</b>", normal_style))
    content.append(Paragraph(f"Invoice Number: <b>{receipt.invoice.invoice_number}</b>", normal_style))
    content.append(Spacer(1, 30))
    
    # Payment Amount
    amount_data = [
        ['Amount Paid:', f"${receipt.amount_paid:.2f}"],
    ]
    if receipt.payment_type == 'deposit':
        amount_data.append(['Payment For:', f'Deposit ({receipt.invoice.deposit_percentage}%)'])
        amount_data.append(['Remaining Balance:', f"${receipt.invoice.balance_due:.2f}"])
    elif receipt.payment_type == 'balance':
        amount_data.append(['Payment For:', 'Balance Payment'])
        amount_data.append(['Total Paid:', f"${receipt.invoice.amount_paid:.2f}"])
    else:
        amount_data.append(['Payment For:', 'Full Payment'])
    
    amount_table = Table(amount_data, colWidths=[6*cm, 8*cm])
    amount_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1a365d')),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    content.append(amount_table)
    content.append(Spacer(1, 40))
    
    # Thank You
    content.append(Paragraph("Thank you for your payment!", normal_style))
    content.append(Paragraph(
        f"For inquiries, contact us at {company.email} or {company.phone}",
        normal_style
    ))
    
    # Build PDF
    doc.build(content)
    
    # Get PDF content
    pdf = buffer.getvalue()
    buffer.close()
    # Create response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt_{str(receipt.receipt_number)[:8]}.pdf"'

    return response
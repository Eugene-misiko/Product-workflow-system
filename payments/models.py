"""

Includes:
- Invoice with 70% deposit
- M-Pesa Request and Response
- Payment records
- Receipts

M-Pesa Integration:
- STK Push for payment initiation
- Callback handling for payment confirmation
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
import random
from companies.models import Company
import string
import uuid


class Invoice(models.Model):
    """Invoice with 70% deposit requirement."""
    
    STATUS_DRAFT = 'draft'
    STATUS_PENDING = 'pending'
    STATUS_PARTIAL = 'partial'
    STATUS_PAID = 'paid'
    STATUS_CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_PENDING, 'Pending'),
        (STATUS_PARTIAL, 'Partially Paid'),
        (STATUS_PAID, 'Paid'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]
    
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='invoices')
    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=20, unique=True, blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # 70% Deposit
    deposit_percentage = models.PositiveIntegerField(default=70)
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deposit_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    terms = models.TextField(blank=True, default="70% deposit required before work starts. Payment via M-Pesa.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.invoice_number
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            date_part = timezone.now().strftime('%Y%m%d')
            random_part = ''.join(random.choices(string.digits, k=4))
            self.invoice_number = f"INV-{date_part}-{random_part}"

        if self.order:
            self.subtotal = self.order.subtotal
            self.tax = self.order.tax
            self.delivery_fee = self.order.delivery_fee
            self.discount = self.order.discount
            self.total_amount = self.order.total_price

        # compute deposit from total
        self.deposit_amount = (self.total_amount * self.deposit_percentage) / 100

        if self.pk:
            total_paid = sum(p.amount for p in self.payments.filter(status='completed'))
            deposit_paid = sum(
                p.amount for p in self.payments.filter(
                    status='completed',
                    payment_type='deposit'
                )
            )
        else:
            total_paid = 0
            deposit_paid = 0

        self.amount_paid = total_paid
        self.deposit_paid = deposit_paid
        self.balance_due = self.total_amount - self.amount_paid

        # STATUS LOGIC
        if self.amount_paid >= self.total_amount:
            self.status = self.STATUS_PAID
        elif self.amount_paid >= self.deposit_amount:
            self.status = self.STATUS_PARTIAL
        elif self.amount_paid > 0:
            self.status = self.STATUS_PENDING
        else:
            self.status = self.STATUS_DRAFT

        super().save(*args, **kwargs)
    
    @property
    def is_deposit_paid(self):
        return self.deposit_paid >= self.deposit_amount
    
    @property
    def can_start_work(self):
        return self.is_deposit_paid

class MpesaRequest(models.Model):
    """M-Pesa STK Push Request."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mpesa_requests')
    company = models.ForeignKey(Company,on_delete=models.CASCADE,null=True,blank=True)
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='mpesa_requests')
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='mpesa_requests')
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    account_reference = models.CharField(max_length=50)
    transaction_desc = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.order.order_number} - {self.amount}"


class MpesaResponse(models.Model):
    """M-Pesa STK Push Response."""
    
    request = models.OneToOneField(MpesaRequest, on_delete=models.CASCADE, related_name='response')
    
    merchant_request_id = models.CharField(max_length=255)
    checkout_request_id = models.CharField(max_length=255, unique=True)
    response_code = models.CharField(max_length=10)
    response_description = models.CharField(max_length=255)
    
    is_successful = models.BooleanField(default=False)
    receipt_number = models.CharField(max_length=50, null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    transaction_date = models.CharField(max_length=50, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.checkout_request_id} - {'Success' if self.is_successful else 'Failed'}"


class Payment(models.Model):
    """Payment record."""
    
    STATUS_PENDING = 'pending'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_REFUNDED = 'refunded'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_REFUNDED, 'Refunded'),
    ]
    
    PAYMENT_TYPE_DEPOSIT = 'deposit'
    PAYMENT_TYPE_BALANCE = 'balance'
    PAYMENT_TYPE_FULL = 'full'
    
    PAYMENT_TYPE_CHOICES = [
        (PAYMENT_TYPE_DEPOSIT, 'Deposit (70%)'),
        (PAYMENT_TYPE_BALANCE, 'Balance (30%)'),
        (PAYMENT_TYPE_FULL, 'Full Payment'),
    ]
    
    METHOD_MPESA = 'mpesa'
    METHOD_CASH = 'cash'
    METHOD_CARD = 'card'
    
    METHOD_CHOICES = [
        (METHOD_MPESA, 'M-Pesa'),
        (METHOD_CASH, 'Cash'),
        (METHOD_CARD, 'Card'),
    ]
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='payments')
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    mpesa_response = models.OneToOneField(MpesaResponse, on_delete=models.SET_NULL, null=True, blank=True, related_name='payment')
    payment_number = models.CharField(max_length=20, unique=True, blank=True)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default=PAYMENT_TYPE_DEPOSIT)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES, default=METHOD_MPESA)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    transaction_id = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.payment_number} - {self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.payment_number:
            date_part = timezone.now().strftime('%Y%m%d')
            random_part = ''.join(random.choices(string.digits, k=4))
            self.payment_number = f"PAY-{date_part}-{random_part}"
        super().save(*args, **kwargs)


class Receipt(models.Model):
    """Receipt auto-generated after payment."""
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='receipts')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='receipts')
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='receipts')
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='receipts')
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='receipt', null=True)
    receipt_number = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    mpesa_receipt = models.CharField(max_length=100, blank=True)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    payment_type = models.CharField(max_length=20,choices=Payment.PAYMENT_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Receipt {self.receipt_number}"
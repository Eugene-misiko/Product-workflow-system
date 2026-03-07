from django.db import models
from django.conf import settings
from myapp.models import Product
from accounts.models import User
from cloudinary.models import CloudinaryField
from payments.models import Invoice
from decimal import Decimal

class Order(models.Model):

    STATUS_CHOICES = [
        ("pending_design", "Pending Design"),
        ("design_completed", "Design Completed"),
        ("design_rejected", "Rejected By Designer"),
        ("approved", "Approved For Printing"),
        ("printing", "Printing"),
        ("completed", "Completed"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    quantity = models.PositiveIntegerField(default=1)

    needs_design = models.BooleanField(default=False)

    design_file = CloudinaryField("design", blank=True, null=True)

    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="pending_design"
    )

    rejection_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"
    
def save(self, *args, **kwargs):
    super().save(*args, **kwargs)
    if not hasattr(self, "invoice"):
        total = self.product.price * self.quantity
        deposit = total * 0.7
        Invoice.objects.create(
            user=self.user,
            order=self,
            total_amount=total,
            deposit_amount=deposit)    
        
class Invoice(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("partial", "Partially Paid"),
        ("paid", "Paid"),
    ]
    order = models.OneToOneField("Order",on_delete=models.CASCADE,related_name="invoice")
    invoice_number = models.CharField(max_length=100, unique=True)
    total_amount = models.DecimalField(max_digits=10,decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=10,decimal_places=2)
    balance_due = models.DecimalField(max_digits=10,decimal_places=2)
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.invoice_number        
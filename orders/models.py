from django.db import models
from django.conf import settings
from myapp.models import Product, ProductField
from accounts.models import User
from cloudinary.models import CloudinaryField
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

    order_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )
    total_price = models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)
    needs_design = models.BooleanField(default=False)
    design_file = CloudinaryField(
        "design",
        blank=True,
        null=True
    )
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="pending_design"
    )
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def save(self, *args, **kwargs):
        # Generate order number automatically
        if not self.order_number:
            last_order = Order.objects.order_by("-id").first()
            if last_order and last_order.order_number:
                last_number = int(last_order.order_number.split("-")[1])
                new_number = last_number + 1
            else:
                new_number = 1
            self.order_number = f"ORD-{new_number:03d}"
        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.order_number}"

class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    def save(self, *args, **kwargs):
        self.unit_price = self.product.price
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)    
        order = self.order
        order.total_price = sum(item.subtotal for item in order.items.all())
        order.save()           
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
class OrderItemField(models.Model):
    order_item = models.ForeignKey(OrderItem,on_delete=models.CASCADE,
        related_name="field_values")
    field = models.ForeignKey(ProductField, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)    




        
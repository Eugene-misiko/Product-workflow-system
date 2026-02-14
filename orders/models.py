from django.db import models
from myapp.models import Product
from django.conf import settings
from decimal import Decimal

class Order(models.Model):
    """
    Represents a customer's order.

    An order belongs to one client and contains multiple OrderItems.
    The total price is calculated automatically from its items.
    """

    STATUS = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("in_design", "In Design"),
        ("on_printing", "On Printing"),
        ("on_delivery", "On Delivery"),
        ("completed", "Completed"),
    ]
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS, default="pending")
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    DESIGN_TYPE = [
        ("designed", "Already Designed"),
        ("not_designed", "Not Designed"),]  
    design_type = models.CharField( max_length=20,choices=DESIGN_TYPE,default="not_designed")

    COLOR_CHOICES = [
    ("full_color", "Full Color"),
    ("black_white", "Black & White"),]
    color_type = models.CharField(
        max_length=20,
        choices=COLOR_CHOICES,
        default="full_color")

    def calculate_total(self):
        """
        Recalculate total price from all related order items.
        """
        total = sum(item.price_at_order * item.quantity for item in self.items.all())
        self.total_price = total
        self.save()

    def __str__(self):
        return f"Order #{self.id} - {self.client.username}"
class OrderItem(models.Model):
    """
    Represents a single product inside an order.

    Stores the product price at the time of ordering to
    protect against future price changes.
    """

    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price_at_order = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        """
        Automatically set price_at_order from product price
        if not already provided.
        """
        if not self.price_at_order:
            self.price_at_order = self.product.price
        super().save(*args, **kwargs)
        self.order.calculate_total()



        

from django.db import models
from orders.models import Order
from django.conf import settings
# Create your models here.
class Delivery(models.Model):
    """Delivery note-Represents the delivery information of an order.
        One order has only one delivery record.
        Stores the delivery date.
    """
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_transit", "In Transit"),
        ("delivered", "Delivered"),
        ("failed", "Failed"),
    ]    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )    
    order = models.OneToOneField(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="delivery"
    )
    address = models.TextField()
    phone = models.CharField(max_length=20)    
    delivered_at = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)    
    tracking_number = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    def __str__(self):
        return f"Delivery for Order #{self.order.id}"

class DeliveryIssue(models.Model):

    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_review", "In Review"),
        ("resolved", "Resolved"),
    ]

    delivery = models.ForeignKey(
        Delivery,
        on_delete=models.CASCADE,
        related_name="issues"
    )

    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    description = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="open"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Issue for Order #{self.delivery.order.id}"

from django.db import models
from orders.models import Order
# Create your models here.
class Delivery(models.Model):
    """Delivery note-Represents the delivery information of an order.
        One order has only one delivery record.
        Stores the delivery date.
    """
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    delivered_at = models.DateField()
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_transit", "In Transit"),
        ("delivered", "Delivered"),
        ("failed", "Failed"),
    ]  
    address = models.TextField()
    phone = models.CharField(max_length=20)      

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )
    tracking_number = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )    
    created_at = models.DateTimeField(auto_now_add=True)    
    def __str__(self):
        return f"Delivery for Order #{self.order.id}"
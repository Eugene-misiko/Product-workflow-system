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
    
    def __str__(self):
        return f"Delivery for Order #{self.order.id}"
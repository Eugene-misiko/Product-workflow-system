from django.db import models
from orders.models import Order
# Create your models here.
class Delivery(models.Model):
    """Delivery note"""
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    delivered_at = models.DateField()
from django.db import models
from orders.models import Order
# Create your models here.
class Payment(models.Model):
    """Payments for orders"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    confirmed = models.BooleanField(default=False)
from django.db import models
from myapp.models import Product
from accounts.models import User
# Create your models here.
class Order(models.Model):
    """Client order"""
    STATUS = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("in_production", "In Production"),
        ("delivered", "Delivered"),
    ]
    client = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS, default="pending")
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

class OrderItem(models.Model):
    """Items inside an order"""
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price_at_order = models.DecimalField(max_digits=10, decimal_places=2)

from django.db import models
from django.conf import settings
from orders.models import Order
# Create your models here.
class Message(models.Model):
    """
    Represents a chat message related to a specific order.
    Supports:
    - Client and Admin
    - Admin and Designer
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.username} - Order #{self.order.id}"
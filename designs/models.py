from django.db import models

# Create your models here.
from django.db import models
from orders.models import Order
from accounts.models import User

class Design(models.Model):
    """
    Uploaded design file
    Represents a design file uploaded by a client.
    Used when client selects "Already Designed    
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    file = models.FileField(upload_to="designs/")
    status = models.CharField(max_length=20, default="pending")

    def __str__(self):
        return f"Design for Order #{self.order.id}"    

class DesignRequest(models.Model):
    """Design work request"""
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    designer = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)

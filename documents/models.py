from django.db import models
from orders.models import Order
# Create your models here.
class LegalDocument(models.Model):
    """
    Generated contract
    Represents generated legal contract document
    for a specific order.    
    """
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    file = models.FileField(upload_to="documents/")

    def __str__(self):
        return f"Legal Document for Order #{self.order.id}"    
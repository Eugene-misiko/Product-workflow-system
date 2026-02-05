from django.db import models
from orders.models import Order
# Create your models here.
class LegalDocument(models.Model):
    """Generated contract"""
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    file = models.FileField(upload_to="documents/")
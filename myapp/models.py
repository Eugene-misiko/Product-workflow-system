from django.db import models

class Category(models.Model):
    """Product category"""
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

class Product(models.Model):
    """Sellable product"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)


    
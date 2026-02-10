from django.db import models
from cloudinary.models import CloudinaryField
class Category(models.Model):
    """Product category"""
    BURNERS = "burner"
    BOOKS = "books"
    CARDS= "cards"

    category = [
        (BURNERS, "burners"),
        (BOOKS, "books"),
        (CARDS, "cards"),
    ]    
    name = models.CharField(max_length=100,)
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return self.name
class Product(models.Model):
    """Sellable product"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

class ProductImage(models.Model):
    """Images for products """
    product = models.ForeignKey(Product, related_name="images", on_delete=models.CASCADE)
    image = CloudinaryField('image')

    def __str__(self):
        return f"Image for {self.product.name}"



    
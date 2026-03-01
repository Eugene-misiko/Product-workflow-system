from django.db import models
from cloudinary.models import CloudinaryField

class Product(models.Model):
    CATEGORY_CHOICES = [
        ("banner", "Banner"),
        ("clothes", "Clothes"),
        ("books", "Books"),
        ("cards", "Cards"),
        ("cups", "Cups"),
        ("pens", "Pens"),
        ("flyers", "Flyers"),
        ("others", "Others"),
    ]

    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    image = CloudinaryField("image", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


    
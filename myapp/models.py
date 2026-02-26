from django.db import models
from cloudinary.models import CloudinaryField
from django.urls import reverse
class Category(models.Model):
    name = models.CharField(max_length=250)
    slug = models.SlugField(unique=True)
    class Meta:
        verbose_name_plural ="categories"
    def __str__(self):
       return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, related_name="products", on_delete=models.CASCADE)
    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    image = CloudinaryField('image')
    
    def __str__(self):
        return self.name
    

    def get_absolute_url(self):
        return reverse('products:product_detail', kwargs={'id':self.id, 'slug':self.slug})
class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.email
    

from django.contrib.auth import get_user_model

User = get_user_model()

# Base Product model
class New_Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_available = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

# Card model
class Card(New_Product):
    card_type = models.CharField(max_length=100)  
    size = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField(default=1)

# Banner model
class Banner(New_Product):
    width = models.FloatField()
    height = models.FloatField()
    material = models.CharField(max_length=100) \

# Clothes model
class Clothes(New_Product):
    size = models.CharField(max_length=10)
    color = models.CharField(max_length=50)
    material = models.CharField(max_length=100)

# Book model
class Book(New_Product):
    book_type = models.CharField(max_length=100)  
    cover_type = models.CharField(max_length=50)  
    lamination = models.CharField(max_length=50)  
    binding = models.CharField(max_length=50)     

# Flyer model
class Flyer(New_Product):
    size = models.CharField(max_length=50)
    material = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(default=1)

# Pen model
class Pen(New_Product):
    color = models.CharField(max_length=50)
    pen_type = models.CharField(max_length=50)  

# Envelope model
class Envelope(New_Product):
    size = models.CharField(max_length=50)
    color = models.CharField(max_length=50)
    material = models.CharField(max_length=100)

# Order model
class Item_order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_orders')
    product_type = models.CharField(max_length=50)  
    product_id = models.PositiveIntegerField()  
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product_type} - {self.quantity}"    


    
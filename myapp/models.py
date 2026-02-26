from django.db import models
from cloudinary.models import CloudinaryField
from django.urls import reverse
from django.contrib.auth import get_user_model
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
    
User = get_user_model()


class ItemOrder(models.Model):

    PRODUCT_CHOICES = [
        ('card', 'Card'),
        ('banner', 'Banner'),
        ('clothes', 'Clothes'),
        ('book', 'Book'),
        ('flyer', 'Flyer'),
        ('pen', 'Pen'),
        ('envelope', 'Envelope'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('printing', 'Printing'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders'
    )

    product_type = models.CharField(max_length=20, choices=PRODUCT_CHOICES)

    title = models.CharField(max_length=255)
    description = models.TextField()

    quantity = models.PositiveIntegerField()

    # Card / Flyer / Envelope
    size = models.CharField(max_length=50, blank=True, null=True)

    # Banner
    width = models.FloatField(blank=True, null=True)
    height = models.FloatField(blank=True, null=True)
    material = models.CharField(max_length=100, blank=True, null=True)

    # Book
    cover_type = models.CharField(max_length=50, blank=True, null=True)
    lamination = models.CharField(max_length=50, blank=True, null=True)
    binding = models.CharField(max_length=50, blank=True, null=True)

    # Clothes
    color = models.CharField(max_length=50, blank=True, null=True)

    # Pen
    pen_type = models.CharField(max_length=50, blank=True, null=True)

    # Upload design
    design_file = models.ImageField(upload_to='designs/', blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product_type}"


    
from django.db import models
from cloudinary.models import CloudinaryField
class Category(models.Model):
    CATEGORY_TYPES = [
        ('wedding_card', 'Wedding Card'),
        ('book', 'Book'),
        ('plate', 'Plate'),
        ('hoodie', 'Hoodie'),
        ('nocat', 'No Category'),
        ('calendar', 'Calendar'),
    ]

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, choices=CATEGORY_TYPES, unique=True,)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
class Product(models.Model):
    category_code = models.CharField(max_length=50)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)

    # Printing Specifications
    quantity = models.PositiveIntegerField(default=1)
    color_mode = models.CharField(
        max_length=20,
        choices=[
            ('bw', 'Black & White'),
            ('color', 'Full Color'),
        ],
        default='color'
    )
    # Paper Type (for books, cards, etc.)
    paper_type = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    # Paper Size
    paper_size = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    # Book-specific fields
    number_of_pages = models.PositiveIntegerField(blank=True, null=True)
    has_spine = models.BooleanField(default=False)
    spine_size_mm = models.FloatField(blank=True, null=True)

    # Binding type
    binding_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=[
            ('perfect', 'Perfect Binding'),
            ('spiral', 'Spiral Binding'),
            ('hardcover', 'Hardcover'),
            ('stapled', 'Stapled'),
        ]
    )
    # Apparel specific
    size = models.CharField(max_length=20, blank=True, null=True)
    material = models.CharField(max_length=100, blank=True, null=True)
    # Plate specific
    plate_diameter_cm = models.FloatField(blank=True, null=True)
    # Upload design file
    design_file = models.FileField(upload_to='designs/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name


class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.email


    
from django.db import models
from myapp.models import Product
from django.conf import settings
from decimal import Decimal
from accounts.models import User
from django.core.validators import MinValueValidator

class Order(models.Model):
    """
    Represents a customer's order.
    An order belongs to one client and contains multiple OrderItems.
    The total price is calculated automatically from its items.
    """
    STATUS = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("in_design", "In Design"),
        ("on_printing", "On Printing"),
        ("on_delivery", "On Delivery"),
        ("completed", "Completed"),
    ]
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS, default="pending")
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    DESIGN_TYPE = [
        ("designed", "Already Designed"),
        ("not_designed", "Not Designed"),]  
    design_type = models.CharField( max_length=20,choices=DESIGN_TYPE,default="not_designed")

    COLOR_CHOICES = [
    ("full_color", "Full Color"),
    ("black_white", "Black & White"),]
    color_type = models.CharField(
        max_length=20,
        choices=COLOR_CHOICES,
        default="full_color")

    DELIVERY_MODE = [
        ("uber", "Uber Delivery"),
        ("pickup", "Client Pickup"),
    ]

    delivery_mode = models.CharField(
        max_length=20,
        choices=DELIVERY_MODE,
        null=True,
        blank=True
    )
    DELIVERY_STATUS = [
        ("waiting", "Waiting"),
        ("on_delivery", "On Delivery"),
        ("arrived", "Arrived Safely"),
        ("issue", "Delivery Issue"),
    ]

    delivery_status = models.CharField(
        max_length=20,
        choices=DELIVERY_STATUS,
        default="waiting"
    )


    def calculate_total(self):
        """
        Recalculate total price from all related order items.
        """
        total = sum(item.price_at_order * item.quantity for item in self.items.all())
        self.total_price = total
        self.save()

    def __str__(self):
        return f"Order #{self.id} - {self.client.username}"
    
    
DESIGN_CHOICES = [
    ("designed", "I have my design"),
    ("not_designed", "I want it designed"),
]

PAPER_CHOICES = [
    ("matte", "Matte"),
    ("glossy", "Glossy"),
    ('book_paper', 'Book Paper'),
]

COVER_CHOICES = [
    ("matte", "Matte"),
    ("glossy", "Glossy"),
]

EDIT_CHOICES = [
    ("simple", "Simple editing"),
    ("full", "Full editing"),
]

BINDING_CHOICES = [
    ('perfect', 'Perfect Binding'),
    ('spiral', 'Spiral Binding'),
    ('hardcover', 'Hardcover'),
    ('stapled', 'Stapled'),
]
class OrderCreateForm(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    product = models.CharField(max_length=100)
    quantity = models.IntegerField(validators=[MinValueValidator(1)], blank=False)
    color_type = models.CharField(max_length=50, blank=True)
    design_type = models.CharField(max_length=20,
        choices=DESIGN_CHOICES,
        blank=True,
    )
    description = models.TextField(blank=True)

    # Book / paper fields
    number_of_pages = models.IntegerField(
        validators=[MinValueValidator(1)],
        blank=True
    )
    binding_type = models.CharField(max_length=20,
        choices=BINDING_CHOICES,
        blank=True
    )
    has_spine = models.BooleanField(blank=True)
    spine_size_mm = models.FloatField(blank=True)
    paper_type = models.CharField(max_length=20,
        choices=PAPER_CHOICES,
        blank=True
    )
    cover_type = models.CharField(max_length=20,
        choices=COVER_CHOICES,
        blank=True
    )
    paper_size = models.CharField(max_length=50, blank=True)

    # Apparel fields
    size = models.CharField(max_length=20, blank=True)
    material = models.CharField(max_length=100, blank=True)

    # Plate / banner
    plate_diameter_cm = models.FloatField(blank=True)
    design_file = models.FileField(upload_to='designes/',blank=True) 

class OrderItem(models.Model):
    """
    Represents a single product inside an order.

    Stores the product price at the time of ordering to
    protect against future price changes.
    """

    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    price_at_order = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        """
        Automatically set price_at_order from product price
        if not already provided.
        """
        if not self.price_at_order:
            self.price_at_order = self.product.price
        super().save(*args, **kwargs)
        self.order.calculate_total()

class DesignDetail(models.Model):
    """
    Extra design details when client selects
    'Not Designed'.

    Stores design instructions for designer.
    """
    PAPER_TYPE = [
        ("glossy", "Glossy"),
        ("matte", "Matte"),
        ("bond", "Bond Paper"),]
    EDITING_TYPE = [
        ("basic", "Basic Editing"),
        ("advanced", "Advanced Editing"),]
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    description = models.TextField()
    paper_type = models.CharField(max_length=20, choices=PAPER_TYPE)
    editing_type = models.CharField(max_length=20, choices=EDITING_TYPE)







        

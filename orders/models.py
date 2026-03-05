from django.db import models
from django.conf import settings
from myapp.models import Product
from accounts.models import User
from cloudinary.models import CloudinaryField


class Order(models.Model):

    STATUS_CHOICES = [
        ("pending_design", "Pending Design"),
        ("design_completed", "Design Completed"),
        ("design_rejected", "Rejected By Designer"),
        ("approved", "Approved For Printing"),
        ("printing", "Printing"),
        ("print_rejected", "Rejected By Printer"),
        ("completed", "Completed"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    quantity = models.PositiveIntegerField(default=1)

    needs_design = models.BooleanField(default=False)

    design_file = CloudinaryField("design", blank=True, null=True)

    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="pending_design"
    )

    rejection_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Custom User model with role-based access control.
    """

    CLIENT = "client"
    ADMIN = "admin"
    DESIGNER = "designer"

    ROLE_CHOICES = [
        (CLIENT, "Client"),
        (ADMIN, "Admin"),
        (DESIGNER, "Designer"),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=CLIENT,
        help_text="Defines the role of the user in the system"
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="User phone number"
    )

    def __str__(self):
        return f"{self.username} ({self.role})"



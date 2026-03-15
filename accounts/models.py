from django.contrib.auth.models import AbstractUser
from django.db import models
from .managers import UserManager


class User(AbstractUser):
    """
    Custom User model with role-based access control.
    """
    username = None

    CLIENT = "client"
    ADMIN = "admin"
    DESIGNER = "designer"
    PRINTER = "printer"

    ROLE_CHOICES = [
        (CLIENT, "Client"),
        (ADMIN, "Admin"),
        (DESIGNER, "Designer"),
        (PRINTER, "Printer"),
    ]

    # Make email unique
    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=CLIENT,
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
    )
    first_name = models.CharField(max_length=150, unique=True)
    last_name = models.CharField(max_length=150)
    USERNAME_FIELD = "first_name"
    REQUIRED_FIELDS = ["email"]
    # use custom manager
    objects = UserManager()

    def __str__(self):
        return f"{self.first_name} - {self.role}"
from django.contrib.auth.models import AbstractUser
from django.db import models
from .managers import UserManager
from cloudinary.models import CloudinaryField


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
    avatar = CloudinaryField("avatar",folder="avatars", blank=True, null=True)
    phone = models.CharField(
        max_length=20,
        blank=True,
    )
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name"]
    # use custom manager
    objects = UserManager()

    def __str__(self):
        return f"{self.first_name} - {self.role}"
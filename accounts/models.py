from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import UserManager
# Create your models here.

class Role(models.Model):
    CLIENT = "CLIENT"
    ADMIN = "ADMIN"
    DESIGNER = "DESIGNER"

    ROLE_CHOICES = [
        (CLIENT, "CLIENT"),
        (ADMIN, "ADMIN"),
        (DESIGNER, "DESIGNER"),
    ]

    name = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True )

    def __str__(self):
        return self.name
    
class User(AbstractBaseUser, PermissionsMixin):  
    email = models.EmailField(unique=True)  
    full_name= models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True)

    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    objects = UserManager()

    def __str__(self):
        return self.email


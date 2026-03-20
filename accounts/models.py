"""
User Model - Custom User with Role-Based Access Control
Supports: Admin, Designer, Printer, Client
Includes Invitation System
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import secrets
import string


class User(AbstractUser):
    """
    Custom User model with role-based access control.
    Admin is created via management command (single admin per company).
    Other users are invited by admin.
    """
    username = None  # Remove username field
    # Roles
    ADMIN = 'admin'
    DESIGNER = 'designer'
    PRINTER = 'printer'
    CLIENT = 'client'
    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (DESIGNER, 'Designer'),
        (PRINTER, 'Printer'),
        (CLIENT, 'Client'),
    ]
    # Core Fields
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=CLIENT)
    # Company (for multi-tenant)
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='users',
        null=True,
        blank=True
    )
    
    # Profile Information
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    # Email Verification
    email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Settings
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name']
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"
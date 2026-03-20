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
    
    def clean(self):
        super().clean()
        # Prevent creating multiple admins
        if self.role == self.ADMIN:
            existing_admin = User.objects.filter(
                role=self.ADMIN,
                company=self.company
            ).exclude(pk=self.pk).first()
            
            if existing_admin:
                raise ValidationError(
                    "Each company can only have one admin account."
                )
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def full_name(self):
        return self.get_full_name()
    
    @property
    def is_admin(self):
        return self.role == self.ADMIN
    
    @property
    def is_designer(self):
        return self.role == self.DESIGNER
    
    @property
    def is_printer(self):
        return self.role == self.PRINTER
    
    @property
    def is_client(self):
        return self.role == self.CLIENT   
class Invitation(models.Model):
    """
    Invitation model for inviting users to join the system.
    Admin creates invitations and sends them via email.
    """
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_EXPIRED = 'expired'
    STATUS_CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_EXPIRED, 'Expired'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]
    
    # Token for invitation link
    token = models.CharField(max_length=64, unique=True, editable=False)
    
    # Who sent the invitation
    invited_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_invitations'
    )
    
    # Invitation details
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=User.ROLE_CHOICES)
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='invitations'
    )
    
    # Personal message
    message = models.TextField(blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    
    # User who accepted (linked after registration)
    accepted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accepted_invitation'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Invitation to {self.email} as {self.role}"
    
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = self.generate_token()
        if not self.expires_at:
            # Invitation expires in 7 days
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs) 

    @staticmethod
    def generate_token():
        """Generate a secure random token"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(64))
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        return self.status == self.STATUS_PENDING and not self.is_expired
    
    def accept(self, user):
        """Mark invitation as accepted"""
        self.status = self.STATUS_ACCEPTED
        self.accepted_by = user
        self.accepted_at = timezone.now()
        self.save()
    
    def expire(self):
        """Mark invitation as expired"""
        self.status = self.STATUS_EXPIRED
        self.save()
    
    def cancel(self):
        """Cancel the invitation"""
        self.status = self.STATUS_CANCELLED
        self.save()

class PasswordResetToken(models.Model):
    """
    Token for password reset functionality
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.token:
            alphabet = string.ascii_letters + string.digits
            self.token = ''.join(secrets.choice(alphabet) for _ in range(64))
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(hours=24)
        super().save(*args, **kwargs)  
    @property
    def is_valid(self):
        return not self.used and timezone.now() < self.expires_at
    
    def mark_used(self):
        self.used = True
        self.save()              

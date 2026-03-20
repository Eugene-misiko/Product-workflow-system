"""
Account Models - Custom User with Role-Based Access Control.

Supports multi-tenant architecture where:
- Each company has its own admin
- Each company has its own users (designers, printers, clients)
- Users are isolated to their company

User Roles:
- PLATFORM_ADMIN: Platform superuser (manages multiple companies)
- ADMIN: Company admin (one per company, manages company)
- DESIGNER: Company designer (handles design orders)
- PRINTER: Company printer (handles printing jobs)
- CLIENT: Client (places orders)

No complex management commands needed - admin is created through:
1. Company registration (first user becomes admin)
2. Django admin panel
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
    
    Multi-tenant Support:
    - Each user belongs to a company
    - Users can only see data from their company
    - Company admin can manage company users
    
    User Creation Flow:
    - Platform Admin: Created via Django admin or createsuperuser
    - Company Admin: Created when company registers
    - Staff (Designer/Printer): Invited by company admin
    - Client: Registers via invitation link
    
    Attributes:
        company: The company this user belongs to
        role: User's role (admin, designer, printer, client)
        email: Email (unique, used for login)
        phone: Phone number
        avatar: Profile picture
    """
    
    username = None  # Remove username field
    
    # Roles
    PLATFORM_ADMIN = 'platform_admin'
    ADMIN = 'admin'
    DESIGNER = 'designer'
    PRINTER = 'printer'
    CLIENT = 'client'
    
    ROLE_CHOICES = [
        (PLATFORM_ADMIN, 'Platform Admin'),
        (ADMIN, 'Company Admin'),
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
        blank=True,
        help_text='Company this user belongs to (null for platform admin)'
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
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    def clean(self):
        """Validate user data."""
        super().clean()
        
        # Platform admin should not have a company
        if self.role == self.PLATFORM_ADMIN and self.company:
            raise ValidationError(
                "Platform admin should not be assigned to a company."
            )
        
        # Non-platform users must have a company
        if self.role != self.PLATFORM_ADMIN and not self.company:
            raise ValidationError(
                "Non-platform users must be assigned to a company."
            )
    
    @property
    def is_platform_admin(self):
        """Check if user is platform admin."""
        return self.role == self.PLATFORM_ADMIN
    
    @property
    def is_company_admin(self):
        """Check if user is company admin."""
        return self.role == self.ADMIN
    
    @property
    def is_designer(self):
        """Check if user is designer."""
        return self.role == self.DESIGNER
    
    @property
    def is_printer(self):
        """Check if user is printer."""
        return self.role == self.PRINTER
    
    @property
    def is_client(self):
        """Check if user is client."""
        return self.role == self.CLIENT
    
    @property
    def is_staff_member(self):
        """Check if user is company staff (admin, designer, or printer)."""
        return self.role in [self.ADMIN, self.DESIGNER, self.PRINTER]


class Invitation(models.Model):
    """
    User Invitation System.
    Company admins can invite:
    - Designers
    - Printers
    - Clients
    
    Invitation Flow:
    1. Admin creates invitation with email and role
    2. System sends email with registration link
    3. User clicks link and completes registration
    4. User is assigned to admin's company with specified role
    
    Attributes:
        token: Unique token for invitation link
        company: Company the user will join
        invited_by: User who sent the invitation
        email: Recipient email
        role: Role the user will have
        status: Current status of invitation
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
    
    # Company
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='invitations'
    )
    
    # Invitation details
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=User.ROLE_CHOICES)
    
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
        return f"Invitation to {self.email} as {self.get_role_display()}"
    
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = self.generate_token()
        if not self.expires_at:
            # Invitation expires in 7 days
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_token():
        """Generate a secure random token."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(64))
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        return self.status == self.STATUS_PENDING and not self.is_expired
    
    def accept(self, user):
        """Mark invitation as accepted."""
        self.status = self.STATUS_ACCEPTED
        self.accepted_by = user
        self.accepted_at = timezone.now()
        self.save()
    
    def expire(self):
        """Mark invitation as expired."""
        self.status = self.STATUS_EXPIRED
        self.save()
    
    def cancel(self):
        """Cancel the invitation."""
        self.status = self.STATUS_CANCELLED
        self.save()


class PasswordResetToken(models.Model):
    """
    Token for password reset functionality.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens'
    )
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


class UserProfile(models.Model):
    """
    Extended profile information for users.
    This model stores additional user information and statistics
    that are not essential for authentication.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    
    # Additional Info
    bio = models.TextField(blank=True)
    
    # For Clients
    company_name = models.CharField(max_length=200, blank=True)
    company_address = models.TextField(blank=True)
    
    # Statistics
    total_orders = models.PositiveIntegerField(default=0)
    completed_jobs = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Preferences
    notification_preferences = models.JSONField(default=dict, blank=True)
    # Social
    website = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()}'s Profile"
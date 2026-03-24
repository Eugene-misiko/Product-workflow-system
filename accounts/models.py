"""
Custom User model with role-based access control.
Multi-tenant support - each user belongs to a company.
User Roles:
- PLATFORM_ADMIN: Platform superuser (createsuperuser)
- ADMIN: Company admin (created via registration)
- DESIGNER: Company designer (invited by admin)
- PRINTER: Company printer (invited by admin)  
- CLIENT: Client (invited by admin or self-register)
Admin is created via:
1. Platform Admin: python manage.py createsuperuser
2. Company Admin: POST /api/auth/register-company/
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
import secrets
import string
from .managers import UserManager
class User(AbstractUser):
    """
    Custom User model with role-based access control.
    """
    #objects = UserManager()
    username = None
    objects = UserManager()
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
    
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=CLIENT)
    
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='users',
        null=True,
        blank=True
    )
    
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    
    email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name']
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    @property
    def is_platform_admin(self):
        return self.role == self.PLATFORM_ADMIN
    @property
    def is_staff(self):
        return self.role in [self.ADMIN, self.DESIGNER, self.PRINTER] or self.is_superuser
    @property
    def is_company_admin(self):
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
    
    @property
    def is_staff_member(self):
        return self.role in [self.ADMIN, self.DESIGNER, self.PRINTER]

    """
        Restricts the platfoem admin from creating it's own company
    """
    def clean(self):

        if self.role == self.PLATFORM_ADMIN and self.company is not None:

            raise ValidationError("Platform admin cannot belong to a company")

        if self.role != self.PLATFORM_ADMIN and self.company is None:
            raise ValidationError("Non-platform users must belong to a company")
         

class Invitation(models.Model):
    """
    User invitation system for company staff and clients.
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
    
    token = models.CharField(max_length=64, unique=True, editable=False)
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='invitations')
    
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=User.ROLE_CHOICES)
    message = models.TextField(blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    accepted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='accepted_invitation')
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Invitation to {self.email} as {self.get_role_display()}"
    
    def save(self, *args, **kwargs):
        if not self.token:
            alphabet = string.ascii_letters + string.digits
            self.token = ''.join(secrets.choice(alphabet) for _ in range(64))
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        return self.status == self.STATUS_PENDING and not self.is_expired
    
    def accept(self, user):
        user.company = self.company
        user.role = self.role
        user.save()

        self.status = self.STATUS_ACCEPTED
        self.accepted_by = user
        self.accepted_at = timezone.now()
        self.save()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['email', 'company'],
                condition=models.Q(status='pending'),
                name='unique_pending_invitation_per_email_company'
            )
        ]           


class PasswordResetToken(models.Model):
    """Password reset token."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=64, unique=True, db_index=True)
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
    """Extended user profile."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    bio = models.TextField(blank=True)
    company_name = models.CharField(max_length=200, blank=True)
    company_address = models.TextField(blank=True)
    
    total_orders = models.PositiveIntegerField(default=0)
    completed_jobs = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    notification_preferences = models.JSONField(default=dict, blank=True)
    
    website = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()}'s Profile"
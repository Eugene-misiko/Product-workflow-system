"""
Multi-tenant architecture where each company is a separate tenant.
Each company has its own admin, users, products, orders, and payments.
"""
from django.db import models
from django.conf import settings
import string
import random
from cloudinary.models import CloudinaryField
import uuid
def generate_company_code():
    """Generate unique company code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

class Company(models.Model):
    """
    Company/Tenant model for multi-tenant architecture.
    
    Each company is a separate printing business with:
    - One admin user
    - Multiple designers, printers, and clients
    - Own products, categories, orders, and payments
    """
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    code = models.CharField(max_length=10, unique=True, default=generate_company_code)
    logo = CloudinaryField('image', folder='company/') 
    
    # Contact
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='Kenya')
    website = models.URLField(blank=True)
    
    # Domain
    custom_domain = models.CharField(max_length=255, blank=True, unique=True, null=True)
    subdomain = models.CharField(max_length=100, blank=True, unique=True, null=True)
    
    # Admin (One per company)
    admin = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_company'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Subscription
    SUBSCRIPTION_PLANS = [
        ('free', 'Free Trial'),
        ('starter', 'Starter'),
        ('professional', 'Professional'),
        ('enterprise', 'Enterprise'),
    ]
    subscription_plan = models.CharField(max_length=20, choices=SUBSCRIPTION_PLANS, default='free')
    subscription_active = models.BooleanField(default=True)
    subscription_starts = models.DateField(null=True, blank=True)
    subscription_expires = models.DateField(null=True, blank=True)
    
    # Business Settings
    currency = models.CharField(max_length=10, default='KES')
    currency_symbol = models.CharField(max_length=5, default='KSh')
    deposit_percentage = models.PositiveIntegerField(default=70)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Companies'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    @property
    def staff_count(self):
        return self.users.filter(role__in=['designer', 'printer']).count()
    
    @property
    def clients_count(self):
        return self.users.filter(role='client').count()
    
    @property
    def orders_count(self):
        return self.orders.count()


class CompanySettings(models.Model):
    """
    Detailed settings for each company including M-Pesa credentials.
    """
    
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='settings')
    
    # Working Hours
    working_days = models.JSONField(default=list, blank=True)
    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True)
    timezone = models.CharField(max_length=50, default='Africa/Nairobi')
    
    # Notifications
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    
    # Payment Methods
    accept_mpesa = models.BooleanField(default=True)
    accept_cash = models.BooleanField(default=True)
    accept_card = models.BooleanField(default=False)
    accept_bank_transfer = models.BooleanField(default=True)
    
    # Company M-Pesa Credentials
    mpesa_shortcode = models.CharField(max_length=10, blank=True)
    mpesa_passkey = models.CharField(max_length=100, blank=True)
    mpesa_consumer_key = models.CharField(max_length=100, blank=True)
    mpesa_consumer_secret = models.CharField(max_length=100, blank=True)
    
    # Delivery
    offer_pickup = models.BooleanField(default=True)
    offer_delivery = models.BooleanField(default=True)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    free_delivery_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Social
    facebook = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    whatsapp_number = models.CharField(max_length=20, blank=True)
    
    # Terms
    terms_conditions = models.TextField(blank=True)
    privacy_policy = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Company Settings'
    
    def __str__(self):
        return f"{self.company.name} Settings"

class CompanyInvitation(models.Model):
    """
    Platform-level invitation for new companies to join.
    Sent by platform admin.
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
    company_slug = models.SlugField(null=True, blank=True)
    email = models.EmailField()
    company_name = models.CharField(max_length=200)
    message = models.TextField(blank=True, null=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='company_invitations_sent'
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = uuid.uuid4().hex
        super().save(*args, **kwargs)   
    def generate_token():
        return uuid.uuid4().hex

    token = models.CharField(max_length=64, unique=True, default=generate_token, editable=False)         

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Company Invitation: {self.company_name}"
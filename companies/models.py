"""
Company Models - Multi-tenant Architecture.

Each company is a separate tenant with:
- Its own admin
- Its own users
- Its own orders
- Its own products
- Its own settings
"""
from django.db import models
from django.conf import settings
import string
import random
def generate_company_code():
    """Generate unique company code for identification."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
class Company(models.Model):
    """
    Company/Tenant model for multi-tenant architecture.
    Each company is a separate printing business that:
    - Has its own admin user
    - Has its own staff (designers, printers)
    - Has its own clients
    - Has its own products and categories
    - Has its own orders and payments
    - Has its own settings
    Data Isolation:
    - All queries are filtered by company
    - Users can only see their company's data
    - Each company has unique subdomain or custom domain

    Attributes:
        name: Company name
        slug: URL-friendly identifier
        code: Unique company code (for identification)
        admin: The admin user for this company
        logo: Company logo
        email: Company email
        phone: Company phone
        address: Company address
        is_active: Whether company is active
        subscription_plan: Current subscription
    """
    # Basic Info
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    code = models.CharField(max_length=10, unique=True, default=generate_company_code)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    
    # Contact Information
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Kenya')
    website = models.URLField(blank=True)
    
    # Domain Configuration
    custom_domain = models.CharField(max_length=255, blank=True, unique=True, null=True)
    subdomain = models.CharField(max_length=100, blank=True, unique=True, null=True)
    
    # Admin User (One admin per company)
    admin = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_company',
        help_text='The admin user who manages this company'
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
    subscription_plan = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_PLANS,
        default='free'
    )
    subscription_active = models.BooleanField(default=True)
    subscription_starts = models.DateField(null=True, blank=True)
    subscription_expires = models.DateField(null=True, blank=True)
    # Business Settings
    currency = models.CharField(max_length=10, default='KES')
    currency_symbol = models.CharField(max_length=5, default='KSh')
    deposit_percentage = models.PositiveIntegerField(
        default=70,
        help_text='Percentage deposit required before work starts (default 70%)'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Companies'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    @property
    def staff_count(self):
        """Get count of staff members (designers + printers)."""
        return self.users.filter(role__in=['designer', 'printer']).count()
    
    @property
    def clients_count(self):
        """Get count of clients."""
        return self.users.filter(role='client').count()
    
    @property
    def orders_count(self):
        """Get total orders count."""
        return self.orders.count()


class CompanySettings(models.Model):
    """
    Detailed settings for each company.
    
    These settings control:
    - Working hours
    - Notification preferences
    - Payment methods
    - Delivery options
    - Social media links
    """
    
    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        related_name='settings'
    )
    
    # Working Hours
    working_days = models.JSONField(
        default=list,
        blank=True,
        help_text='List of working days e.g. ["monday", "tuesday", ...]'
    )
    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True)
    timezone = models.CharField(max_length=50, default='Africa/Nairobi')
    
    # Notification Settings
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    
    # Payment Settings
    accept_mpesa = models.BooleanField(default=True)
    accept_cash = models.BooleanField(default=True)
    accept_card = models.BooleanField(default=False)
    accept_bank_transfer = models.BooleanField(default=True)
    
    # M-Pesa Settings (Each company can have their own)
    mpesa_shortcode = models.CharField(max_length=10, blank=True)
    mpesa_passkey = models.CharField(max_length=100, blank=True)
    mpesa_consumer_key = models.CharField(max_length=100, blank=True)
    mpesa_consumer_secret = models.CharField(max_length=100, blank=True)
    
    # Delivery Settings
    offer_pickup = models.BooleanField(default=True)
    offer_delivery = models.BooleanField(default=True)
    delivery_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    free_delivery_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Free delivery for orders above this amount'
    )
    
    # Social Media
    facebook = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    whatsapp_number = models.CharField(max_length=20, blank=True)
    
    # Terms and Policies
    terms_conditions = models.TextField(blank=True)
    privacy_policy = models.TextField(blank=True)
    
    # Email Templates
    invoice_email_template = models.TextField(
        blank=True,
        help_text='Custom email template for invoices'
    )
    receipt_email_template = models.TextField(
        blank=True,
        help_text='Custom email template for receipts'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Company Settings'
    
    def __str__(self):
        return f"{self.company.name} Settings"


class CompanyInvitation(models.Model):
    """
    Invitation for new company registration.
    
    Platform superuser can invite new companies to join.
    When accepted, the invitee becomes the company admin.
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
    
    token = models.CharField(max_length=64, unique=True)
    email = models.EmailField()
    company_name = models.CharField(max_length=200)
    
    # Who sent the invitation (platform superuser)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='company_invitations_sent'
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    
    # Company created after accepting
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invitation'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Company Invitation: {self.company_name}"
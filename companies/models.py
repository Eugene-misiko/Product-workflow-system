"""
Company Model - Multi-tenant Architecture
Each company has its own isolated data
"""
from django.db import models
from django.conf import settings
# Create your models here.
class Company(models.Model):
    """
    Company/Tenant model for multi-tenant architecture.
    Each company represents a separate printing business.
    """
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    
    # Contact Information
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    website = models.URLField(blank=True)
    
    # Business Settings
    currency = models.CharField(max_length=10, default='USD')
    currency_symbol = models.CharField(max_length=5, default='$')
    deposit_percentage = models.PositiveIntegerField(default=50)  # % deposit required
    
    # Subscription
    SUBSCRIPTION_PLANS = [
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('professional', 'Professional'),
        ('enterprise', 'Enterprise'),
    ]
    subscription_plan = models.CharField(max_length=20, choices=SUBSCRIPTION_PLANS, default='free')
    subscription_active = models.BooleanField(default=True)
    subscription_expires = models.DateField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Settings
    settings = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name_plural = 'Companies'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    @property
    def admin_user(self):
        """Get the admin user for this company"""
        return self.users.filter(role='admin').first()
class CompanySettings(models.Model):
    """
    Detailed settings for each company
    """
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='company_settings')
    
    # Working Hours
    working_days = models.JSONField(default=list)  # ['monday', 'tuesday', ...]
    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True)
    
    # Notification Settings
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    
    # Payment Settings
    accept_cash = models.BooleanField(default=True)
    accept_card = models.BooleanField(default=True)
    accept_mobile_money = models.BooleanField(default=False)
    
    # Delivery Settings
    offer_pickup = models.BooleanField(default=True)
    offer_delivery = models.BooleanField(default=True)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Social Media
    facebook = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.company.name} Settings"        
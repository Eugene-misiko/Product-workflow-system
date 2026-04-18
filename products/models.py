"""
Product and Category models for printing products.
Each company has its own products and categories.
"""
from django.db import models
from django.conf import settings
from cloudinary.models import CloudinaryField
from django.core.exceptions import ValidationError
from django.utils.text import slugify
# Create your models here.
class Category(models.Model):
    """Product category (company-specific)."""
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='categories'
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(blank=True)
    description = models.TextField(blank=True)
    image = CloudinaryField('image', folder='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']
        unique_together = ['company', 'slug']
        indexes = [
            models.Index(fields=['company']),
            models.Index(fields=['company', 'is_active']),
        ]       
    
    def __str__(self):
        return self.name
    
    def generate_unique_slug(self):
        base_slug = slugify(self.name)
        slug = base_slug
        counter = 1
        
        while Product.objects.filter(company=self.company, slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_unique_slug()
        super().save(*args, **kwargs)
    # def clean(self):
    #     if self.category.company != self.company:
    #         raise ValidationError("Category must belong to the same company as the product.")        
  
class Product(models.Model):
    """Product/Service offered by a printing company."""
    
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='products'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products'
    )
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    image = CloudinaryField('image', folder='products/',  blank=True, null=True) 
    gallery = models.JSONField(default=list, blank=True)
    
    min_quantity = models.PositiveIntegerField(default=1)
    max_quantity = models.PositiveIntegerField(default=10000)
    
    requires_design = models.BooleanField(default=False)
    design_templates = models.JSONField(default=list, blank=True)
    
    print_specs = models.JSONField(default=dict, blank=True)
    has_quantity_pricing = models.BooleanField(default=False)
    quantity_pricing = models.JSONField(default=list, blank=True)
    
    production_time = models.PositiveIntegerField(default=24, help_text='Hours')
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
            verbose_name_plural = 'Products'
            ordering = ['-created_at']
            unique_together = ['company', 'slug']
            indexes = [
                models.Index(fields=['company'], name='product_company_idx'),
                models.Index(fields=['company', 'is_active'], name='product_company_active_idx'),
                models.Index(fields=['category'], name='product_category_idx'),
            ]           
    def __str__(self):
        return f"{self.name} - {self.company.name}"
    
    def generate_unique_slug(self):
        base_slug = slugify(self.name)
        slug = base_slug
        counter = 1
        
        while Product.objects.filter(company=self.company, slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_unique_slug()
        super().save(*args, **kwargs)
    
    def get_price_for_quantity(self, quantity):
        if not self.has_quantity_pricing:
            return self.price
        
        for tier in sorted(self.quantity_pricing, key=lambda x: x.get('min_qty', 0), reverse=True):
            if quantity >= tier.get('min_qty', 0):
                return tier.get('price', self.price)
        
        return self.price

class ProductField(models.Model):
    """Custom fields for products (dynamic form fields)."""
    
    FIELD_TYPES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('textarea', 'Text Area'),
        ('select', 'Select'),
        ('checkbox', 'Checkbox'),
        ('file', 'File Upload'),
        ('date', 'Date'),
    ]
    company = models.ForeignKey('companies.Company',on_delete=models.CASCADE,related_name='product_fields')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='fields')
    name = models.CharField(max_length=100)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    required = models.BooleanField(default=True)
    options = models.JSONField(default=list, blank=True)
    placeholder = models.CharField(max_length=200, blank=True)
    help_text = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    def save(self, *args, **kwargs):
        if not self.company:
            self.company = self.product.company
        super().save(*args, **kwargs)    
    
    class Meta:
        ordering = ['order']
        indexes = [
            models.Index(fields=['company'], name='productfield_company_idx'),
        ]   
    def __str__(self):
        return f"{self.product.name} - {self.name}"
    def clean(self):
        if self.product.company != self.company:
            raise ValidationError("ProductField company must match product company.")    
from django.contrib import admin
from .models import Product,Category, ProductField
# Register your models here.
admin.site.register(Product)
admin.site.register(ProductField)
admin.site.register(Category)

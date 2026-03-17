from django.contrib import admin
from .models import Order,OrderItemField,OrderItem,Invoice
# Register your models here
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(OrderItemField)
admin.site.register(Invoice)

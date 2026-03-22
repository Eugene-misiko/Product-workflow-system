from django.contrib import admin
from .models import Order,OrderItem,OrderItemFieldValue,OrderStatusHistory,PrintJob,Transportation
# Register your models here
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(OrderItemFieldValue)
admin.site.register(OrderStatusHistory)
admin.site.register(PrintJob)
admin.site.register(Transportation)
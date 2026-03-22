from django.contrib import admin
from .models import MpesaRequest, MpesaResponse,Invoice, Payment,Receipt

# Register your models here.
admin.site.register(MpesaRequest)
admin.site.register(MpesaResponse)
admin.site.register(Payment)
admin.site.register(Receipt)
admin.site.register(Invoice)


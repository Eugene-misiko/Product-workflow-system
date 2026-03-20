from django.contrib import admin
from .models import MpesaRequest, MpesaResponse

# Register your models here.
admin.site.register(MpesaRequest)
admin.site.register(MpesaResponse)

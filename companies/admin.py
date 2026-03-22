from django.contrib import admin
from .models import Company,CompanySettings,CompanyInvitation
# Register your models here.
admin.site.register(Company)
admin.site.register(CompanySettings)
admin.site.register(CompanyInvitation)
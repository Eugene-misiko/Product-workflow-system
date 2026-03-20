from django.contrib import admin
from .models import User,UserProfile,Invitation, PasswordResetToken

# Register your models here.
admin.site.register(User)
admin.site.register(UserProfile)
admin.site.register(Invitation)
admin.site.register(PasswordResetToken)



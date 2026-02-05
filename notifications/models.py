from django.db import models
from accounts.models import User
# Create your models here.

class Notification(models.Model):
    """System notifications"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)

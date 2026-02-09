from django.db import models
from accounts.models import User
# Create your models here.
class AuditLog(models.Model):
    """
    Sytem audit logs 
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    details = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
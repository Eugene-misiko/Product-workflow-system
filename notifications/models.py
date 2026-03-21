from django.db import models
from django.conf import settings
from django.utils import timezone


class Notification(models.Model):
    """User notifications."""
    TYPE_ORDER = 'order'
    TYPE_PAYMENT = 'payment'
    TYPE_DESIGN = 'design'
    TYPE_PRINTING = 'printing'
    TYPE_DELIVERY = 'delivery'
    TYPE_SYSTEM = 'system'
    TYPE_CHOICES = [
        (TYPE_ORDER, 'Order'),
        (TYPE_PAYMENT, 'Payment'),
        (TYPE_DESIGN, 'Design'),
        (TYPE_PRINTING, 'Printing'),
        (TYPE_DELIVERY, 'Delivery'),
        (TYPE_SYSTEM, 'System'),
    ]
    
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='notifications')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.URLField(blank=True)
    related_object_type = models.CharField(max_length=50, blank=True)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)

    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email}: {self.title}"
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
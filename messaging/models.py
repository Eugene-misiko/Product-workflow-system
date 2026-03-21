from django.db import models
from django.conf import settings
# Create your models here.
class Conversation(models.Model):
    """Conversation between users."""
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='conversations')
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, null=True, blank=True, related_name='conversations')
    title = models.CharField(max_length=200, blank=True)
    last_message = models.TextField(blank=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    last_message_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='last_messages'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-last_message_at']
    
    def __str__(self):
        return self.title or f"Conversation #{self.id}"
class Message(models.Model):
    """Individual message."""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    attachments = models.JSONField(default=list, blank=True)
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    read_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='read_messages', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.email}: {self.content[:50]}"

from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from .models import Notification
from .serializers import NotificationSerializer
# Create your views here.
class NotificationViewSet(ModelViewSet):
    """
    User notifications.
    """
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

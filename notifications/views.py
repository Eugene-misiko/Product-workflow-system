from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from .models import Notification
from .serializers import NotificationSerializer
# Create your views here.
class NotificationViewSet(ModelViewSet):
    """
    Notifications for clients, designers, and admins.
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

    def get_queryset(self):
        """
        Users see only their notifications.
        """        
        user = self.request.user
        return Notification.objects.filter(user=user)
    

def notification_list_template(request):
    """
    Display notifications for the logged-in user.
    """
    if not request.user.is_authenticated:
        return render(request, "forbidden.html", status=403)

    notifications = Notification.objects.filter(user=request.user)
    return render(request, "notification_list.html", {"notifications": notifications})    

from .models import Notification

def notify(user, message):
    """
    Create a notification for a given user.
    
    Args:
        user: User instance who will receive the notification
        message: String message for the notification
    """
    if user is not None and message:
        Notification.objects.create(user=user, message=message)


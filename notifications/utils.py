from .models import Notification

def notify(user, company, title, message, notification_type="system", **kwargs):
    """"
    Helper function to create a notification.
    """
    Notification.objects.create(
        user=user,
        company=company,
        title=title,
        message=message,
        notification_type=notification_type,
        **kwargs
    )


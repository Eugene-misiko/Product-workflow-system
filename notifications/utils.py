from .models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()

def create_notification(user, message):
    """
    Create a notification for a single user.
    """
    if not user:
        return None

    return Notification.objects.create(
        user=user,
        message=message
    )


def create_bulk_notification(users, message):
    """
    Create the same notification for multiple users.
    """
    notifications = [
        Notification(user=user, message=message)
        for user in users
    ]
    return Notification.objects.bulk_create(notifications)


def mark_notification_as_read(notification):
    """
    Mark a single notification as read.
    """
    notification.is_read = True
    notification.save()
    return notification


def mark_all_as_read(user):
    """
    Mark all notifications for a user as read.
    """
    return Notification.objects.filter(
        user=user,
        is_read=False
    ).update(is_read=True)


def get_unread_count(user):
    """
    Return number of unread notifications for a user.
    """
    return Notification.objects.filter(
        user=user,
        is_read=False
    ).count()

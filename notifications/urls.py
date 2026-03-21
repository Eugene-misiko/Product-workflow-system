from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('notifications/', views.NotificationListView.as_view(), name='list'),
    path('notifications/<int:pk>/', views.NotificationDetailView.as_view(), name='detail'),
    path('notifications/<int:pk>/mark-read/', views.MarkAsReadView.as_view(), name='mark_read'),
    path('notifications/mark-all-read/', views.MarkAllReadView.as_view(), name='mark_all_read'),
    path('notifications/unread-count/', views.UnreadCountView.as_view(), name='unread_count'),
]

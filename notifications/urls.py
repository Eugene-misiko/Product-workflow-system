from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, notification_list_template
from django.urls import path
router = DefaultRouter()
router.register("notifications", NotificationViewSet)

urlpatterns = router.urls
urlpatterns += [
    path("view/notifications/", notification_list_template, name="notification_list_template"),
]
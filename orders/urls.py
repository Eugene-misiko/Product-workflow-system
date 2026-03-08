from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, download_invoice
from django.urls import path
router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='orders')

urlpatterns = [
    path("invoice/<int:pk>/download/", download_invoice),
]
urlpatterns += router.urls
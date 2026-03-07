from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, get_invoice
from django.urls import path
router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='orders')

urlpatterns = [
    path("invoice/<int:pk>/", get_invoice)
]
urlpatterns += router.urls
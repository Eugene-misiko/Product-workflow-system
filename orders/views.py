from django.shortcuts import render
from .serializers import OrderSerializer
from rest_framework.viewsets import ModelViewSet
from .models import Order
# Create your views here.
class OrderViewSet(ModelViewSet):
    """Client creates orders, admin views all"""
    serializer_class = OrderSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            return Order.objects.all()
        return Order.objects.filter(client=user)

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)

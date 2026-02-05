from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from .models import Delivery
from .serializers import DeliverySerializer
# Create your views here.

class DeliveryViewSet(ModelViewSet):
    """
    Delivery tracking.
    """
    queryset = Delivery.objects.all()
    serializer_class = DeliverySerializer

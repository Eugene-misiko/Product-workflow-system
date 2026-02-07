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
# adding delivery template for visualisation 

def delivery_list_template(request):
    """
    Admin-only: Display all deliveries in an HTML table.
    """
    if not request.user.is_authenticated or request.user.role != "admin":
        return render(request, "forbidden.html", status=403)

    deliveries = Delivery.objects.all()
    return render(request, "delivery_list.html", {"deliveries": deliveries})
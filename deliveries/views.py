from django.shortcuts import render, get_object_or_404, redirect
from rest_framework.viewsets import ModelViewSet
from .models import Delivery
from orders.models import Order
from django.contrib.auth.decorators import login_required
from .serializers import DeliverySerializer
from django.utils import timezone
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
@login_required
def create_delivery(request, order_id):

    if request.user.role != "admin":
        return render(request, "forbidden.html", status=403)

    order = get_object_or_404(Order, id=order_id)

    # Prevent duplicate delivery
    if hasattr(order, "delivery"):
        return redirect("order_detail", order_id=order.id)

    if request.method == "POST":
        address = request.POST.get("address")
        phone = request.POST.get("phone")
        tracking_number = request.POST.get("tracking_number")

        Delivery.objects.create(
            order=order,
            address=address,
            phone=phone,
            tracking_number=tracking_number
        )

        order.status = "on_delivery"
        order.save()

        return redirect("order_detail", order_id=order.id)

    return render(request, "create_delivery.html", {"order": order})

@login_required
def update_delivery_status(request, order_id):

    if request.user.role != "admin":
        return render(request, "forbidden.html", status=403)

    order = get_object_or_404(Order, id=order_id)

    if not hasattr(order, "delivery"):
        return redirect("order_detail", order_id=order.id)

    delivery = order.delivery

    if request.method == "POST":
        new_status = request.POST.get("status")
        delivery.status = new_status

        if new_status == "delivered":
            delivery.delivered_at = timezone.now()
            order.status = "completed"
            order.save()

        delivery.save()

        return redirect("order_detail", order_id=order.id)

    return render(request, "deliveries/update_delivery.html", {"delivery": delivery})

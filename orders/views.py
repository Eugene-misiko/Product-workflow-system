from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer
from .permissions import CanAccessOrder
from django.shortcuts import render
# Create your views here.
class OrderViewSet(ModelViewSet):
    """
    Order management with status control.
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [CanAccessOrder]

    def get_queryset(self):
        """
        Admin sees all orders.
        Client sees only their own orders.
        """        
        user = self.request.user
        if user.role == "admin":
            return Order.objects.all()
        return Order.objects.filter(client=user)

    def perform_create(self, serializer):
        """
        Assign authenticated user as the client.
        """
        serializer.save(client=self.request.user)

    @action(detail=True, methods=["put"])
    def status(self, request, pk=None):
        """
        Admin updates order status.
        """
        order = self.get_object()
        if request.user.role != "admin":
            return Response({"error": "Forbidden"}, status=403)

        order.status = request.data.get("status")
        order.save()
        return Response({"message": "Status updated"})

#views for backend templates

def order_list_template(request):
    """
    Display orders in an HTML table.
    Admin sees all orders, client sees their own orders.
    """
    if not request.user.is_authenticated:
        return render(request, "forbidden.html", status=403)

    user = request.user
    if user.role == "admin":
        orders = Order.objects.all()
    else:
        orders = Order.objects.filter(client=user)

    return render(request, "order_list.html", {"orders": orders})

def order_detail_template(request, order_id):
    """
    Display a single order and its items.
    """
    if not request.user.is_authenticated:
        return render(request, "forbidden.html", status=403)

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return render(request, "not_found.html", {"message": "Order not found."}, status=404)

    if request.user.role != "admin" and order.client != request.user:
        return render(request, "forbidden.html", status=403)

    items = order.items.all()
    return render(request, "order_detail.html", {"order": order, "items": items})
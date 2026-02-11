from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer
from .permissions import CanAccessOrder
from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from notifications.utils import notify
from audit.utils import audit_log
from .forms import OrderForm

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
@login_required
def order_create(request):
    """
    Client creates an order (HTML form).
    """
    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.client = request.user  # attach current user as client
            order.save()
            return redirect("orders_list")
    else:
        form = OrderForm()

    return render(request, "order_form.html", {"form": form})

def orders_list(request):
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


@login_required
def order_approve(request, order_id):
    """
    Admin approves an order.
    """
    if request.user.role != "admin":
        return render(request, "403.html", status=403)

    order = Order.objects.get(id=order_id)
    order.status = "confirmed"
    order.save()

    notify(order.client, f"Your order #{order.id} was approved.")
    audit_log(request.user, "APPROVE_ORDER", f"Order {order.id}")

    return redirect("orders_list")


@login_required
def order_reject(request, order_id):
    """
    Admin rejects an order.
    """
    if request.user.role != "admin":
        return render(request, "403.html", status=403)

    order = Order.objects.get(id=order_id)
    order.status = "pending"
    order.save()

    notify(order.client, f"Your order #{order.id} was rejected.")
    audit_log(request.user, "REJECT_ORDER", f"Order {order.id}")

    return redirect("orders_list")


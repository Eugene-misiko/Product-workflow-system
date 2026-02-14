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
from .forms import OrderCreateForm

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
    Create a new order with one product item.

    Workflow:
    - User selects category
    - User selects product
    - User enters quantity
    - Order is created
    - OrderItem is created
    - Total price calculated automatically
    """

    if request.user.role != "client":
        return render(request, "forbidden.html", status=403)

    if request.method == "POST":
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            category = form.cleaned_data["category"]
            product = form.cleaned_data["product"]
            quantity = form.cleaned_data["quantity"]

            # Create order
            order = Order.objects.create(client=request.user)

            # Create order item
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price_at_order=product.price
            )

            return redirect("order_detail", order_id=order.id)

    else:
        form = OrderCreateForm()

    return render(request, "order_form.html", {"form": form})

def orders_list(request):
    """
    Render a list of orders for the current user.

    - Admin sees all orders.
    - Clients see only their own orders.
    Orders are sorted by creation date, newest first.
    """

    user = request.user

    # Admin sees all orders
    if user.role == "admin":
        orders = Order.objects.all().order_by('-created_at')
    else:
        # Client sees only their own orders
        orders = Order.objects.filter(client=user).order_by('-created_at')

   
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
    order.status = "approved"
    order.rejection_reason = None
    order.save()
    notify(order.client, f"Your order #{order.id} has been approved.")
    audit_log(request.user, "APPROVE_ORDER", f"Order {order.id}")
    return redirect("orders_list")

@login_required
def order_reject(request, order_id):
    """
    Admin rejects an order and provides reason.
    """
    if request.user.role != "admin":
        return render(request, "403.html", status=403)
    order = Order.objects.get(id=order_id)
    if request.method == "POST":
        reason = request.POST.get("reason")
        order.status = "rejected"
        order.rejection_reason = reason
        order.save()
        notify(order.client, f"Your order #{order.id} was rejected. Reason: {reason}")
        audit_log(request.user, "REJECT_ORDER", f"Order {order.id}")
        return redirect("orders_list")
    return render(request, "reject_order.html", {"order": order})



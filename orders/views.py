from django.contrib import messages
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Order, OrderItem, DesignDetail
from .serializers import OrderSerializer, OrderItemSerializer
from .permissions import CanAccessOrder
from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from notifications.utils import notify
from audit.utils import audit_log
from .forms import OrderCreateForm
from accounts.models import User
from myapp.models import Category
from myapp.models import Product
from django.http import JsonResponse
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
    - User selects color
    - User selects design type (designed/not designed)
    - Order and OrderItem created
    - If not designed, create DesignDetail
    - If designed, redirect to upload_design page
    """
    if request.user.role != "client":
        return render(request, "forbidden.html", status=403)

    categories = Category.objects.filter(is_active=True)

    if request.method == "POST":
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            category = form.cleaned_data["category"]
            product = form.cleaned_data["product"]
            quantity = form.cleaned_data["quantity"]
            color = form.cleaned_data["color"]
            design_type = form.cleaned_data.get("design_type")

            # Create order
            order = Order.objects.create(client=request.user)

            # Create order item
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price_at_order=product.price,
                color=color
            )

            # Handle design type
            if design_type == "not_designed":
                description = form.cleaned_data.get("description")
                paper_type = form.cleaned_data.get("paper_type")
                editing_type = form.cleaned_data.get("editing_type")

                # Create design detail record
                DesignDetail.objects.create(
                    order=order,
                    description=description,
                    paper_type=paper_type,
                    editing_type=editing_type,
                )
                order.status = "in_design"
                order.save()

            elif design_type == "designed":
                # Redirect client to upload their design
                return redirect("upload_design", order_id=order.id)

            return redirect("order_detail", order_id=order.id)

    else:
        form = OrderCreateForm()

    return render(request, "order_form.html", {"form": form, "categories": categories})
@login_required
def products_by_category(request, category_id):
    products = Product.objects.filter(category_id=category_id, is_active=True)
    data = [{"id": p.id, "name": p.name} for p in products]
    return JsonResponse(data, safe=False)

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
        orders = Order.objects.filter(is_deleted=False).order_by('-created_at')
    else:
        # Client sees only their own orders
        orders = Order.objects.filter(client=user).order_by('-created_at')

   
    return render(request, "order_list.html", {"orders": orders})


@login_required
def order_detail_template(request, order_id):
    """
    Display a single order and its items.
    """

    #Prevent access to deleted orders
    order = get_object_or_404(
        Order,
        id=order_id,
        is_deleted=False
    )

    #  Permission control
    if request.user.role != "admin" and order.client != request.user:
        return render(request, "forbidden.html", status=403)

    items = order.items.all()

    return render(request, "order_detail.html", {
        "order": order,
        "items": items
    })

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
    Admin rejects an order with optional reason.
    """
    if request.user.role != "admin":
        return render(request, "forbidden.html", status=403)

    order = get_object_or_404(Order, id=order_id, is_deleted=False)

    if request.method == "POST":
        reason = request.POST.get("reason", "")
        order.status = "pending"  
        order.rejection_reason = reason
        order.save()

        notify(order.client, f"Your order #{order.id} was rejected. Reason: {reason}")
        audit_log(request.user, "REJECT_ORDER", f"Order {order.id}, Reason: {reason}")

        return redirect("orders_list")

    return render(request, "reject_order.html", {"order": order})

@login_required
def move_to_design(request, order_id):
    """
    Admin moves approved order to design stage.
    """
    if request.user.role != "admin":
        return render(request, "403.html", status=403)
    order = Order.objects.get(id=order_id)
    if order.status == "approved":
        order.status = "in_design"
        order.save()
        notify(order.client, f"Your order #{order.id} is now in design stage.")
    return redirect("order_detail", order_id=order.id)

@login_required
def move_to_printing(request, order_id):
    """
    Admin marks order as printing.
    """
    if request.user.role != "admin":
        return render(request, "403.html", status=403)
    order = Order.objects.get(id=order_id)
    if order.status == "in_design":
        order.status = "on_printing"
        order.save()
        notify(order.client, f"Your order #{order.id} is now being printed.")
    return redirect("order_detail", order_id=order.id)

@login_required
def move_to_delivery(request, order_id):
    """
    Admin marks order as out for delivery.
    """
    if request.user.role != "admin":
        return render(request, "403.html", status=403)
    order = Order.objects.get(id=order_id)
    if order.status == "on_printing":
        order.status = "on_delivery"
        order.save()
        notify(order.client, f"Your order #{order.id} is now out for delivery.")
    return redirect("order_detail", order_id=order.id)

@login_required
def confirm_delivery(request, order_id):
    """
    Client confirms order was received safely.
    """
    order = Order.objects.get(id=order_id)

    if order.client != request.user:
        return render(request, "403.html", status=403)

    if order.status == "on_delivery":
        order.status = "completed"
        order.save()

        notify(order.client, f"Order #{order.id} marked as completed.")
    
    return redirect("order_detail", order_id=order.id)

@login_required
def choose_delivery_mode(request, order_id):
    """
    Client selects delivery mode:
    - Uber
    - Pickup
    """

    order = get_object_or_404(Order, id=order_id)

    if order.client != request.user:
        return render(request, "forbidden.html", status=403)

    if request.method == "POST":
        mode = request.POST.get("delivery_mode")

        order.delivery_mode = mode
        order.status = "on_delivery"
        order.delivery_status = "on_delivery"
        order.save()

        notify(order.client, f"Your order #{order.id} is now on delivery.")

        return redirect("order_detail", order_id=order.id)

    return render(request, "choose_delivery.html", {"order": order})

@login_required
def confirm_arrival(request, order_id):
    """
    Client confirms delivery arrived safely.
    """

    order = get_object_or_404(Order, id=order_id)

    if order.client != request.user:
        return render(request, "forbidden.html", status=403)

    order.delivery_status = "arrived"
    order.status = "completed"
    order.save()

    notify(order.client, f"Order #{order.id} marked as completed.")

    return redirect("order_detail", order_id=order.id)

@login_required
def report_delivery_issue(request, order_id):
    """
    Client reports delivery problem.
    """

    order = get_object_or_404(Order, id=order_id)

    if order.client != request.user:
        return render(request, "forbidden.html", status=403)

    if request.method == "POST":
        reason = request.POST.get("reason")

        order.delivery_status = "issue"
        order.save()

        admins = User.objects.filter(role="admin")
        for admin in admins:
            notify(admin, f"Delivery issue reported for Order #{order.id}: {reason}")

        return redirect("order_detail", order_id=order.id)

    return render(request, "delivery_issue.html", {"order": order})

@login_required
def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, is_deleted=False)

    #permission control
    if request.user.role == "client":
        if order.client != request.user:
            return render(request, "forbidden.html", status=403)

        if order.status != "pending":
            messages.error(request, "You can only delete pending orders.")
            return redirect("order_detail", order_id=order.id)

    elif request.user.role != "admin":
        return render(request, "forbidden.html", status=403)
    
    # Confirm Delete
    if request.method == "POST":
        order.is_deleted = True
        order.save()

        messages.success(request, "Order deleted successfully.")
        return redirect("orders_list")

    return render(request, "delete_order.html", {"order": order})


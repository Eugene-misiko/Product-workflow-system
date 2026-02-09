from django.shortcuts import render,redirect
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from .models import Payment,Order
from .serializers import PaymentSerializer
from django.contrib.auth.decorators import login_required
from .forms import PaymentForm

# Create your views here

class PaymentViewSet(ModelViewSet):
    """
    Payment handling with backend enforcement.
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    @action(detail=True, methods=["put"])
    def confirm(self, request, pk=None):
        """
        Admin confirms a payment.
        """
        if request.user.role != "admin":
            return Response({"error": "Forbidden"}, status=403)

        payment = self.get_object()
        payment.confirmed = True
        payment.save()
        return Response({"message": "Payment confirmed"})

    @action(detail=False, methods=["get"], url_path="summary/(?P<order_id>[^/.]+)")
    def summary(self, request, order_id=None):
        """
        View payment summary for an order.
        """
        total_paid = Payment.objects.filter(
            order_id=order_id, confirmed=True
        ).aggregate(Sum("amount"))["amount__sum"] or 0

        return Response({"total_paid": total_paid})
    
 #adding views for the payment   
@login_required
def payments_list(request):
    """
    Payments list page (HTML).
    Admin sees all payments.
    Client sees own payments.
    """
    if request.user.role == "admin":
        payments = Payment.objects.all()
    else:
        payments = Payment.objects.filter(order__client=request.user)

    return render(request, "payment_list.html", {
        "payments": payments
    })


@login_required
def payment_create(request, order_id):
    """
    Client creates a payment (HTML form).
    """
    order = Order.objects.get(id=order_id)

    if order.client != request.user:
        return render(request, "403.html", status=403)

    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.order = order
            payment.save()
            return redirect("payments_list")
    else:
        form = PaymentForm()

    return render(request, "payment_form.html", {"form": form})



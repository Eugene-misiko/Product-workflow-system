from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from .models import Payment
from .serializers import PaymentSerializer
# Create your views here.
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
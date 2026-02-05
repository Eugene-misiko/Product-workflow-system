from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer
from .permissions import CanAccessOrder
# Create your views here.
class OrderViewSet(ModelViewSet):
    """
    Order management with status control.
    """
    serializer_class = OrderSerializer
    permission_classes = [CanAccessOrder]

    def get_queryset(self):
        user = self.request.user
        return Order.objects.all() if user.role == "admin" else Order.objects.filter(client=user)

    def perform_create(self, serializer):
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

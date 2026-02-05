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

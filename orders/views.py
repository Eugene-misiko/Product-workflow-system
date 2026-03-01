from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Order
from .serializers import OrderSerializer
from accounts.permissions import IsAdmin

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_queryset(self):
        user = self.request.user

        # Admin sees everything
        if user.role == "admin":
            return Order.objects.all()

        # Designer sees assigned orders
        if user.role == "designer":
            return Order.objects.filter(assigned_designer=user)

        # Client sees only own orders
        return Order.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
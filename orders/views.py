from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Order
from .serializers import OrderSerializer
from accounts.permissions import IsAdmin

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    def get_queryset(self):
        user = self.request.user

        if user.role == "admin":
            return Order.objects.all()

        if user.role == "designer":
            return Order.objects.filter(assigned_designer=user)

        return Order.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    
    """
    Here admin only can approve the order not any other user(design or client)
    """
    @action(detail=True, methods=["put"])
    def approve(self, request, pk=None):
        if request.user.role != "admin":
            return Response({"error": "Only admin can approve"}, status=403)

        order = self.get_object()
        order.status = "approved"
        order.rejection_reason = ""
        order.save()

        return Response({"message": "Order approved successfully"})
    """
    Admin only can reject the order not any user
    """
    @action(detail=True, methods=["put"])
    def reject(self, request, pk=None):
        if request.user.role != "admin":
            return Response({"error": "Only admin can reject"}, status=403)

        reason = request.data.get("reason")
        if not reason:
            return Response({"error": "Rejection reason required"}, status=400)

        order = self.get_object()
        order.status = "rejected"
        order.rejection_reason = reason
        order.save()

        return Response({"message": "Order rejected successfully"})
    """
    Admin can assign orders/admin can control orders,
    """
    @action(detail=True, methods=["put"])
    def assign(self, request, pk=None):
        if request.user.role != "admin":
            return Response({"error": "Only admin can assign designers"}, status=403)

        designer_id = request.data.get("designer_id")

        if not designer_id:
            return Response({"error": "Designer ID required"}, status=400)

        from django.contrib.auth import get_user_model
        User = get_user_model()

        try:
            designer = User.objects.get(id=designer_id, role="designer")
        except User.DoesNotExist:
            return Response({"error": "Designer not found"}, status=404)

        order = self.get_object()
        order.assigned_designer = designer
        order.status = "in_design"
        order.save()

        return Response({"message": "Designer assigned successfully"})
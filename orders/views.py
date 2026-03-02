from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model
from .models import Order
from .serializers import OrderSerializer


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    # Role-based order visibility
    def get_queryset(self):
        user = self.request.user

        if user.role == "admin":
            return Order.objects.all()

        if user.role == "client":
            return Order.objects.filter(user=user)

        if user.role == "designer":
            return Order.objects.filter(assigned_designer=user)

        if user.role == "printer":
            return Order.objects.filter(status="in_print")

        return Order.objects.none()

    #  Client creates order
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    #  Admin assigns designer
    @action(detail=True, methods=["put"])
    def assign(self, request, pk=None):
        if request.user.role != "admin":
            return Response(
                {"error": "Only admin can assign designers"},
                status=status.HTTP_403_FORBIDDEN
            )

        designer_id = request.data.get("designer_id")

        if not designer_id:
            return Response(
                {"error": "Designer ID required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        User = get_user_model()

        try:
            designer = User.objects.get(id=designer_id, role="designer")
        except User.DoesNotExist:
            return Response(
                {"error": "Designer not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        order = self.get_object()
        order.assigned_designer = designer
        order.status = "in_design"
        order.save()

        return Response({"message": "Designer assigned successfully"})

    #  Designer marks ready for print
    @action(detail=True, methods=["put"])
    def mark_ready_for_print(self, request, pk=None):
        if request.user.role != "designer":
            return Response(
                {"error": "Only designer can mark ready for print"},
                status=status.HTTP_403_FORBIDDEN
            )

        order = self.get_object()

        if order.assigned_designer != request.user:
            return Response(
                {"error": "You are not assigned to this order"},
                status=status.HTTP_403_FORBIDDEN
            )

        order.status = "in_print"
        order.save()

        return Response({"message": "Order moved to printing stage"})

    # Printer approves order
    @action(detail=True, methods=["put"])
    def approve(self, request, pk=None):
        if request.user.role != "printer":
            return Response(
                {"error": "Only printer can approve"},
                status=status.HTTP_403_FORBIDDEN
            )

        order = self.get_object()
        order.status = "completed"
        order.rejection_reason = ""
        order.save()

        return Response({"message": "Order approved by printer"})

    #  Printer rejects order
    @action(detail=True, methods=["put"])
    def reject(self, request, pk=None):
        if request.user.role != "printer":
            return Response(
                {"error": "Only printer can reject"},
                status=status.HTTP_403_FORBIDDEN
            )

        reason = request.data.get("reason")
        if not reason:
            return Response(
                {"error": "Rejection reason required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        order = self.get_object()
        order.status = "rejected"
        order.rejection_reason = reason
        order.save()

        return Response({"message": "Order rejected by printer"})
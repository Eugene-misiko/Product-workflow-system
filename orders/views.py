from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Order
from .serializers import OrderSerializer


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    # ROLE BASED VISIBILITY
    def get_queryset(self):
        user = self.request.user

        if user.role == "admin":
            return Order.objects.all()

        # Designer sees only orders waiting for design
        if user.role == "designer":
            return Order.objects.filter(
                needs_design=True,
                status__in=["pending_design", "design_rejected"]
            )

        # Printer sees only completed designs
        if user.role == "printer":
            return Order.objects.filter(status="design_completed")

        # Client sees only their own orders
        return Order.objects.filter(user=user)

    # CLIENT CREATES ORDER
    def perform_create(self, serializer):
        order = serializer.save(user=self.request.user)

        if order.needs_design:
            order.status = "pending_design"
        else:
            order.status = "design_completed"

        order.save()

    # DESIGNER COMPLETES DESIGN
    @action(detail=True, methods=["put"])
    def design_complete(self, request, pk=None):
        if request.user.role != "designer":
            return Response({"error": "Only designer allowed"}, status=403)

        order = self.get_object()

        order.status = "design_completed"
        order.rejection_reason = ""
        order.save()

        return Response({"message": "Design completed successfully"})

    # DESIGNER REJECTS
    @action(detail=True, methods=["put"])
    def design_reject(self, request, pk=None):
        if request.user.role != "designer":
            return Response({"error": "Only designer allowed"}, status=403)

        reason = request.data.get("reason")
        if not reason:
            return Response({"error": "Rejection reason required"}, status=400)

        order = self.get_object()
        order.status = "design_rejected"
        order.rejection_reason = reason
        order.save()

        return Response({"message": "Order rejected by designer"})

    # PRINTER APPROVES
    @action(detail=True, methods=["put"])
    def approve(self, request, pk=None):
        if request.user.role != "printer":
            return Response({"error": "Only printer allowed"}, status=403)

        order = self.get_object()

        if order.status != "design_completed":
            return Response({"error": "Design not completed"}, status=400)

        order.status = "approved"
        order.save()

        return Response({"message": "Order approved for printing"})

    # PRINTER REJECTS
    @action(detail=True, methods=["put"])
    def print_reject(self, request, pk=None):
        if request.user.role != "printer":
            return Response({"error": "Only printer allowed"}, status=403)

        reason = request.data.get("reason")
        if not reason:
            return Response({"error": "Rejection reason required"}, status=400)

        order = self.get_object()
        order.status = "print_rejected"
        order.rejection_reason = reason
        order.save()

        return Response({"message": "Order rejected by printer"})
    @action(detail=True, methods=["put"])
    def mark_in_print(self, request, pk=None):
        if request.user.role != "printer":
            return Response({"error": "Only printer allowed"}, status=403)

        order = self.get_object()

        if order.status != "approved":
            return Response({"error": "Order not approved yet"}, status=400)

        order.status = "in_print"
        order.save()

        return Response({"message": "Printing started"})


    # PRINTER MARKS COMPLETED
    @action(detail=True, methods=["put"])
    def mark_completed(self, request, pk=None):
        if request.user.role != "printer":
            return Response({"error": "Only printer allowed"}, status=403)

        order = self.get_object()

        if order.status != "in_print":
            return Response({"error": "Order not in printing stage"}, status=400)

        order.status = "completed"
        order.save()

        return Response({"message": "Order completed successfully"})
    # PRINTER START PRINTING
    @action(detail=True, methods=["put"])
    def start_printing(self, request, pk=None):
        if request.user.role != "printer":
            return Response({"error": "Only printer allowed"}, status=403)

        order = self.get_object()

        if order.status != "approved":
            return Response({"error": "Order not approved yet"}, status=400)

        order.status = "printing"
        order.save()

        return Response({"message": "Printing started"})


    # PRINTER COMPLETE PRINT
    @action(detail=True, methods=["put"])
    def complete_print(self, request, pk=None):
        if request.user.role != "printer":
            return Response({"error": "Only printer allowed"}, status=403)

        order = self.get_object()

        if order.status != "printing":
            return Response({"error": "Order not printing"}, status=400)

        order.status = "completed"
        order.save()

        return Response({"message": "Printing completed"})
    
from rest_framework import status, generics, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Order, OrderItem, PrintJob, Transportation, OrderStatusHistory
from .serializers import (
    OrderSerializer, OrderDetailSerializer, CreateOrderSerializer,
    AssignDesignerSerializer, AssignPrinterSerializer,
    SubmitDesignSerializer, ApproveDesignSerializer,
    PrintJobSerializer, TransportationSerializer
)
from accounts.models import User
from notifications.models import Notification

class OrderViewSet(viewsets.ModelViewSet):
    """Order CRUD and workflow."""
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Order.objects.filter(company=user.company)
        
        if user.role == User.CLIENT:
            queryset = queryset.filter(user=user)
        elif user.role == User.DESIGNER:
            queryset = queryset.filter(assigned_designer=user)
        elif user.role == User.PRINTER:
            queryset = queryset.filter(assigned_printer=user)
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateOrderSerializer
        if self.action in ['retrieve', 'update', 'partial_update']:
            return OrderDetailSerializer
        return OrderSerializer
    
    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            company=self.request.user.company
        )


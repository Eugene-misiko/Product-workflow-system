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

class AssignDesignerView(APIView):
    """Assign designer to order (admin only)."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, company=request.user.company)
        
        if not order.can_assign_designer:
            return Response({'error': 'Cannot assign designer to this order.'}, status=400)
        
        serializer = AssignDesignerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        designer = get_object_or_404(
            User,
            id=serializer.validated_data['designer_id'],
            role=User.DESIGNER,
            company=request.user.company
        )
        
        order.assigned_designer = designer
        order.status = Order.STATUS_ASSIGNED_TO_DESIGNER
        order.save()
        
        OrderStatusHistory.objects.create(
            order=order,
            old_status=Order.STATUS_PENDING,
            new_status=Order.STATUS_ASSIGNED_TO_DESIGNER,
            changed_by=request.user,
            note=f'Assigned to {designer.get_full_name()}'
        )
        
        Notification.objects.create(
            company=order.company,
            user=designer,
            notification_type='order',
            title='New Design Assignment',
            message=f'You have been assigned to design order {order.order_number}',
            related_object_type='order',
            related_object_id=order.id
        )
        
        return Response({'message': 'Designer assigned successfully.'})

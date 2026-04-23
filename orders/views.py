from rest_framework import status, generics, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from decimal import Decimal
from payments.models import Invoice
from rest_framework.parsers import MultiPartParser, FormParser
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
        order = serializer.save(
            user=self.request.user,
            company=self.request.user.company
        )

        # IMPORTANT: reload after items are saved by serializer
        order.refresh_from_db()

        total_amount = order.total_price

        deposit_amount = total_amount * Decimal('0.7')

        Invoice.objects.create(
            company=order.company,
            order=order,
            total_amount=total_amount,
            deposit_amount=deposit_amount,
            balance_due=total_amount,
            status=Invoice.STATUS_PENDING
        )

class AssignDesignerView(APIView):
    """Assign designer to order (admin only)."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, company=request.user.company)

        invoice = getattr(order, 'invoice', None)
        if not invoice or not invoice.is_deposit_paid:
            return Response(
                {'error': 'Deposit must be paid before assigning a designer.'},
                status=400
            )        
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
        
        return Response({'message': 'Designer assigned successfully.'
        , 'order': OrderSerializer(order, context={'request': request}).data})

class AssignPrinterView(APIView):
    """Assign printer to order (admin only)."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, company=request.user.company)
        invoice = getattr(order, 'invoice', None)
        if not invoice or not invoice.is_deposit_paid:
            return Response(
                {'error': 'Deposit must be paid before assigning a printer.'},
                status=400
            )        
        if not order.can_assign_printer:
            return Response({'error': 'Cannot assign printer to this order.'}, status=400)        
        if order.needs_design:
            if order.status != Order.STATUS_APPROVED_FOR_PRINTING:
                return Response({"error": "Order must be approved for printing first."}, status=400)
        else:
            if order.status != Order.STATUS_PENDING:
                return Response({"error": "Order must be pending to assign printer."}, status=400)
        
        serializer = AssignPrinterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        printer = get_object_or_404(
            User,
            id=serializer.validated_data['printer_id'],
            role=User.PRINTER,
            company=request.user.company
        )
        
        order.assigned_printer = printer
        order.status = Order.STATUS_PRINTING_QUEUED
        order.save()
        
        print_job, created = PrintJob.objects.get_or_create(order=order)
        print_job.assigned_printer = printer
        print_job.save()
        Notification.objects.create(
            company=order.company,
            user=printer,
            notification_type='printing',
            title='New Print Job',
            message=f'You have been assigned to print order {order.order_number}',
            related_object_type='order',
            related_object_id=order.id
        )
        
        return Response({'message': 'Printer assigned successfully.'
        , 'order': OrderSerializer(order, context={'request': request}).data})

class StartDesignView(APIView):
    """Designer starts working on an order."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, company=request.user.company)
        
        if request.user != order.assigned_designer:
            return Response({'error': 'You are not assigned to this order.'}, status=403)
        
        if not order.can_start_design:
            return Response({'error': 'Cannot start design on this order.'}, status=400)
        
        order.update_status(
            Order.STATUS_DESIGN_IN_PROGRESS,
            user=request.user,
            note='Design work started'
        )
        
        return Response({'message': 'Design work started.',
        'order': OrderSerializer(order, context={'request': request}).data})


class SubmitDesignView(APIView):
    parser_classes = [MultiPartParser, FormParser] 
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        order = get_object_or_404(
            Order,
            pk=pk,
            assigned_designer=request.user,
            company=request.user.company
        )

        if not order.can_submit_design:
            return Response({'error': 'Cannot submit design at this stage.'}, status=400)
        
        serializer = SubmitDesignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        if serializer.validated_data.get('design_file'):
            order.design_file = serializer.validated_data['design_file']
        
        if serializer.validated_data.get('design_notes'):
            order.design_notes = serializer.validated_data['design_notes']
        
        order.design_completed_at = timezone.now()
        order.status = Order.STATUS_DESIGN_COMPLETED
        order.save()
        
        OrderStatusHistory.objects.create(
            order=order,
            old_status=Order.STATUS_DESIGN_IN_PROGRESS,
            new_status=Order.STATUS_DESIGN_COMPLETED,
            changed_by=request.user,
            note='Design submitted for approval'
        )
        
        Notification.objects.create(
            company=order.company,
            user=order.user,
            notification_type='design',
            title='Design Ready for Review',
            message=f'Your design for order {order.order_number} is ready for review',
            related_object_type='order',
            related_object_id=order.id
        )
        
        return Response({
            'message': 'Design submitted for approval.',
            'order': OrderSerializer(order, context={'request': request}).data
        })


class ApproveDesignView(APIView):
    """Client approves or rejects design."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, company=request.user.company)
        
        if request.user != order.user:
            return Response({'error': 'Only the client can approve the design.'}, status=403)
        
        if not order.can_approve_design:
            return Response({'error': 'Cannot approve design at this stage.'}, status=400)
        
        serializer = ApproveDesignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        if serializer.validated_data['approved']:
            order.update_status(
                Order.STATUS_APPROVED_FOR_PRINTING,
                user=request.user,
                note='Design approved by client'
            )
            
            PrintJob.objects.get_or_create(order=order)
            
            return Response({'message': 'Design approved. Order is ready for printing.'})
        else:
            order.status = Order.STATUS_DESIGN_REJECTED
            order.rejection_reason = serializer.validated_data.get('rejection_reason', '')
            order.design_revisions += 1
            order.save()
            
            OrderStatusHistory.objects.create(
                order=order,
                old_status=Order.STATUS_DESIGN_COMPLETED,
                new_status=Order.STATUS_DESIGN_REJECTED,
                changed_by=request.user,
                note=f'Design rejected: {order.rejection_reason}'
            )
            
            if order.assigned_designer:
                Notification.objects.create(
                    company=order.company,
                    user=order.assigned_designer,
                    notification_type='design',
                    title='Design Rejected',
                    message=f'Design for order {order.order_number} was rejected. Reason: {order.rejection_reason}',
                    related_object_type='order',
                    related_object_id=order.id
                )
            
            return Response({'message': 'Design rejected. Designer has been notified.', 'order': OrderSerializer(order, context={'request': request}).data})


class CancelOrderView(APIView):
    """Cancel an order."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, company=request.user.company)
        
        if order.status in [Order.STATUS_COMPLETED, Order.STATUS_CANCELLED]:
            return Response({'error': 'Cannot cancel this order.'}, status=400)
        old_status = order.status 
        reason = request.data.get('reason', '')
        order.status = Order.STATUS_CANCELLED
        order.cancellation_reason = reason
        order.save()
        
        OrderStatusHistory.objects.create(
            order=order,
            old_status=old_status, 
            new_status=Order.STATUS_CANCELLED,
            changed_by=request.user,
            note=f'Order cancelled: {reason}'
        )
        
        return Response({'message': 'Order cancelled.', 'order': OrderSerializer(order, context={'request': request}).data})


class PrintJobViewSet(viewsets.ModelViewSet):
    """Print job management."""
    
    permission_classes = [IsAuthenticated]
    serializer_class = PrintJobSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = PrintJob.objects.filter(order__company=user.company)
        
        if user.role == User.PRINTER:
            queryset = queryset.filter(assigned_printer=user)
        
        return queryset.order_by('-created_at')


class StartPrintJobView(APIView):
    """Start printing."""
    permission_classes = [IsAuthenticated]
    def post(self, request, pk):
        print_job = get_object_or_404(PrintJob, order__id=pk, order__company=request.user.company)
        print_job.start()
        return Response({'message': 'Printing started.'}, status=200)


class MoveToPolishingView(APIView):
    """Move to polishing phase."""
    permission_classes = [IsAuthenticated]
    def post(self, request, pk):
        print_job = get_object_or_404(PrintJob, order__id=pk, order__company=request.user.company)
        print_job.move_to_polishing()
        return Response({'message': 'Moved to polishing phase.'})


class CompletePrintJobView(APIView):
    """Mark print job as completed."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        print_job = get_object_or_404(PrintJob, order__id=pk, order__company=request.user.company)
        print_job.complete()
        
        Notification.objects.create(
            company=print_job.order.company,
            user=print_job.order.user,
            notification_type='order',
            title='Order Ready',
            message=f'Your order {print_job.order.order_number} is ready for pickup/delivery.',
            related_object_type='order',
            related_object_id=print_job.order.id
        )
        
        return Response({'message': 'Print job completed.'})


class TransportationViewSet(viewsets.ModelViewSet):
    """Transportation/Delivery management."""
    
    permission_classes = [IsAuthenticated]
    serializer_class = TransportationSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = Transportation.objects.filter(order__company=user.company)
        
        if user.role == User.CLIENT:
            queryset = queryset.filter(order__user=user)
        
        return queryset.order_by('-created_at')


# Dashboard Views
class ClientOrderListView(generics.ListAPIView):
    """List orders for current client."""
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).order_by('-created_at')


class DesignerAssignmentListView(generics.ListAPIView):
    """List orders assigned to current designer."""
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        return Order.objects.filter(
            assigned_designer=self.request.user
        ).exclude(status__in=[Order.STATUS_COMPLETED, Order.STATUS_CANCELLED]).order_by('-created_at')
        
class PrinterJobListView(generics.ListAPIView):
    """List print jobs assigned to current printer."""
    permission_classes = [IsAuthenticated]
    serializer_class = PrintJobSerializer
    
    def get_queryset(self):
        return PrintJob.objects.filter(
            assigned_printer=self.request.user
        ).exclude(status='completed').order_by('-created_at')


class UnassignedOrdersView(generics.ListAPIView):
    """List orders needing assignment (admin only)."""
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        from django.db.models import Q
        
        return Order.objects.filter(
            company=self.request.user.company,
        ).filter(
            Q(needs_design=True, assigned_designer__isnull=True, status='pending') |
            Q(status='approved_for_printing', assigned_printer__isnull=True)
        ).order_by('-created_at')

class MarkOutForDeliveryView(APIView):
    """Mark transportation as out for delivery."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        transport = get_object_or_404(
            Transportation,
            pk=pk,
            order__company=request.user.company
        )

        transport.status = Transportation.STATUS_IN_TRANSIT
        transport.save()

        transport.order.update_status(
            Order.STATUS_OUT_FOR_DELIVERY,
            user=request.user,
            note="Order is out for delivery"
        )

        return Response({"message": "Marked as out for delivery"})
class MarkDeliveredView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        transport = get_object_or_404(
            Transportation,
            pk=pk,
            order__company=request.user.company
        )

        transport.status = Transportation.STATUS_DELIVERED
        transport.actual_delivery_time = timezone.now()
        transport.save()

        transport.order.update_status(
            Order.STATUS_COMPLETED,
            user=request.user,
            note="Order delivered"
        )

        return Response({"message": "Order delivered successfully"})        

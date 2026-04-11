"""
Company management views including:
- Company details and settings
- Dashboard statistics
- Staff management
"""
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework.generics import ListAPIView
from rest_framework.exceptions import PermissionDenied
from .models import Company, CompanySettings, CompanyInvitation
from django.conf import settings
from .serializers import (
    CompanySerializer, CompanyDetailSerializer,

    CompanySettingsSerializer, CompanyUpdateSerializer,
    DashboardStatsSerializer
)
from accounts.models import User

class CompanyDetailView(generics.RetrieveAPIView):
    """
    Get current company details.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CompanyDetailSerializer
    
    def get_object(self):
        return self.request.user.company


class CompanyListView(ListAPIView):
    queryset = Company.objects.filter(is_active=True)
    serializer_class = CompanySerializer
    permission_classes = []  

class CompanyUpdateView(generics.UpdateAPIView):
    """
    Update company details (admin only).
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CompanyUpdateSerializer
    def get_object(self):
        user = self.request.user
        if not self.request.user.is_company_admin:
            raise PermissionDenied("Only company admin can update company details.")
        return self.request.user.company

class CompanySettingsView(generics.RetrieveUpdateAPIView):
    """
    Get or update company settings (admin only).
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CompanySettingsSerializer
    def get_object(self):
        # Check that the user is a company admin
        if not self.request.user.is_company_admin:  
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only company admin can manage settings.")
        # Get the company
        company = self.request.user.company
        # Get or create the company settings
        settings, _ = CompanySettings.objects.get_or_create(company=company)
        return settings   
class PaymentSettingsView(APIView):
    """
    Get or update payment settings (admin only).
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not request.user.is_company_admin:
            return Response({'error': 'Admin only'}, status=403)
        
        settings, _ = CompanySettings.objects.get_or_create(company=request.user.company)
        
        return Response({
            'accept_mpesa': settings.accept_mpesa,
            'accept_cash': settings.accept_cash,
            'accept_card': settings.accept_card,
            'accept_bank_transfer': settings.accept_bank_transfer,
            'mpesa_shortcode': settings.mpesa_shortcode,
            'mpesa_passkey': settings.mpesa_passkey,
            'mpesa_consumer_key': settings.mpesa_consumer_key,
            'mpesa_consumer_secret': settings.mpesa_consumer_secret,
        })        
    
    def put(self, request):
        if not request.user.is_company_admin:
            return Response({'error': 'Admin only'}, status=403)
        settings, _ = CompanySettings.objects.get_or_create(company=request.user.company)
        settings.accept_mpesa = request.data.get('accept_mpesa', settings.accept_mpesa)
        settings.accept_cash = request.data.get('accept_cash', settings.accept_cash)
        settings.accept_card = request.data.get('accept_card', settings.accept_card)
        settings.accept_bank_transfer = request.data.get('accept_bank_transfer', settings.accept_bank_transfer)
        if request.data.get('mpesa_shortcode'):
            settings.mpesa_shortcode = request.data['mpesa_shortcode']
        if request.data.get('mpesa_passkey'):
            settings.mpesa_passkey = request.data['mpesa_passkey']
        if request.data.get('mpesa_consumer_key'):
            settings.mpesa_consumer_key = request.data['mpesa_consumer_key']
        if request.data.get('mpesa_consumer_secret'):
            settings.mpesa_consumer_secret = request.data['mpesa_consumer_secret']
        settings.save()
        return Response({'message': 'Payment settings updated successfully.'})  

class CompanyDashboardView(APIView):
    """
    Get company dashboard statistics.
    """
    permission_classes = [IsAuthenticated]
    def get(self, request):
        from orders.models import Order
        from payments.models import Invoice, Payment
        company = request.user.company
        
        # Orders
        orders = Order.objects.filter(company=company)
        total_orders = orders.count()
        pending_orders = orders.filter(status='pending').count()
        in_progress = orders.exclude(status__in=['pending', 'completed', 'cancelled']).count()
        completed_orders = orders.filter(status='completed').count()
        
        # Revenue
        total_revenue = Payment.objects.filter(
            company=company,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        pending_payments = Invoice.objects.filter(
            company=company,
            status__in=['pending', 'partial']
        ).aggregate(total=Sum('balance_due'))['total'] or 0
        
        # Users
        total_clients = company.users.filter(role='client').count()
        total_staff = company.users.filter(role__in=['designer', 'printer']).count()
        
        # Recent orders
        recent_orders = orders.order_by('-created_at')[:5]
        recent_orders_data = [
            {
                'id': order.id,
                'order_number': order.order_number,
                'client_name': order.user.get_full_name(),
                'status': order.status,
                'total': str(order.total_price),
                'created_at': order.created_at.isoformat(),
            }
            for order in recent_orders
        ]
        
        return Response({
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'in_progress': in_progress,
            'completed_orders': completed_orders,
            'total_revenue': str(total_revenue),
            'pending_payments': str(pending_payments),
            'total_clients': total_clients,
            'total_staff': total_staff,
            'recent_orders': recent_orders_data,
        })

class StaffListView(generics.ListAPIView):
    """
    List company staff (designers and printers).
    """
    permission_classes = [IsAuthenticated]
    serializer_class = 'accounts.serializers.UserSerializer'
    
    def get_queryset(self):
        return User.objects.filter(
            company=self.request.user.company,
            role__in=['designer', 'printer']
        ).order_by('-created_at')

class StaffStatsView(APIView):
    """
    Get staff statistics.
    """
    permission_classes = [IsAuthenticated]
    def get(self, request):
        company = request.user.company
        
        designers = User.objects.filter(company=company, role='designer')
        printers = User.objects.filter(company=company, role='printer')
        
        return Response({
            'total_designers': designers.count(),
            'total_printers': printers.count(),
            'active_designers': designers.filter(is_active=True).count(),
            'active_printers': printers.filter(is_active=True).count(),
        })
class CompanyInvitationCreateView(APIView):
    """
        invitation view create by platform admin
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != "platform_admin":
            return Response({'error': 'Only platform admin allowed'}, status=403)

        email = request.data.get('email')
        company_name = request.data.get('company_name')
        slug = company_name.lower().replace(" ", "-")
        invitation = CompanyInvitation.objects.create(
            email=email,
            company_name=company_name,
            company_slug=slug,
            message=request.data.get("message", ""),
            invited_by=request.user,
            expires_at=timezone.now() + timezone.timedelta(days=7)
        )

        invite_url = f"{settings.FRONTEND_URL}/store/{invitation.company_slug}/register?token={invitation.token}"

        try:
            send_mail(
                subject='Company Invitation',
                message=f"Register your company here: {invite_url}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            invitation.delete()
            return Response({'error': str(e)}, status=500)

        return Response({'message': 'Invitation sent'})

class CompanyInvitationDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token):
        invitation = get_object_or_404(
            CompanyInvitation,
            token=token,
            status=CompanyInvitation.STATUS_PENDING
        )

        if invitation.expires_at < timezone.now():
            return Response({"error": "Expired"}, status=400)

        return Response({
            "email": invitation.email,
            "company_name": invitation.company_name,
            "is_valid": True
        }) 

class CompanyInvitationCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != "platform_admin":
            return Response({'error': 'Only platform admin allowed'}, status=403)

        invitation = get_object_or_404(CompanyInvitation, id=pk)

        invitation.status = CompanyInvitation.STATUS_CANCELLED
        invitation.save()

        return Response({'message': 'Invitation cancelled'})        
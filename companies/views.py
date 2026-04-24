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
from accounts.serializers import UserSerializer
from .models import Company, CompanySettings, CompanyInvitation
from django.conf import settings
from .serializers import (
    CompanySerializer, CompanyDetailSerializer,

    CompanySettingsSerializer, CompanyUpdateSerializer,
    DashboardStatsSerializer,CompanyInvitationSerializer
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
    serializer_class = UserSerializer
    
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
    Platform-admin-only endpoint to create and email a company-setup
    invitation.
    Request body:
        email        (str) recipient's email address
        company_name (str) the company the admin will register
        message      (str, optional) a personal note in the invite email
    Behaviour:
        1. Validates that the caller is a platform_admin.
        2. Creates a CompanyInvitation record (token auto-generated on the
           model) that expires in 7 days.
        3. Builds an environment-aware registration URL:
              DEBUG  → http://localhost:5173/platform/register-company/?token=…
              PROD   https://<slug>.printflow.com/platform/register-company/?token=…
        4. Sends the invitation email.  If sending fails the invitation row
           is deleted so the DB stays consistent, and a 500 is returned.
    Returns 200 {"message": "Invitation sent", "id": <int>, "token": <str>}
    on success so the frontend can optimistically add the record to state.
    """
    permission_classes = [IsAuthenticated]
 
    def post(self, request):
        if request.user.role != "platform_admin":
            return Response(
                {"error": "Only platform admins can send invitations."},
                status=403,
            )
 
        email = request.data.get("email", "").strip()
        company_name = request.data.get("company_name", "").strip()
 
        if not email:
            return Response({"error": "email is required."}, status=400)
        if not company_name:
            return Response({"error": "company_name is required."}, status=400)
 
        # Normalise the slug the same way the frontend does
        slug = (
            company_name.lower()
            .strip()
            .replace(" ", "-")
        )
        # Remove any characters that are not alphanumeric or hyphens
        import re
        slug = re.sub(r"[^a-z0-9-]+", "", slug)
        slug = slug.strip("-")
 
        invitation = CompanyInvitation.objects.create(
            email=email,
            company_name=company_name,
            company_slug=slug,
            message=request.data.get("message", ""),
            invited_by=request.user,
            expires_at=timezone.now() + timezone.timedelta(days=7),
        )
 
        token = str(invitation.token)
 
        if settings.DEBUG:
            invite_url = (
                f"http://localhost:5173/platform/register-company/"
                f"?token={token}&company={slug}"
            )
        else:
            invite_url = (
                f"https://printflow.vercel.app/{slug}/platform/register-company"
                f"?token={token}"
            )
 
        try:
            send_mail(
                subject="You're invited to set up your company on PrintFlow",
                message=(
                    f"Hello,\n\n"
                    f"{request.user.get_full_name()} has invited you to register "
                    f"your company ({company_name}) on PrintFlow.\n\n"
                    f"Click the link below to get started (expires in 7 days):\n"
                    f"{invite_url}\n\n"
                    f"{'Message: ' + invitation.message if invitation.message else ''}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as exc:
            invitation.delete()
            return Response({"error": str(exc)}, status=500)
 
        serializer = CompanyInvitationSerializer(invitation)
        return Response(
            {"message": "Invitation sent", **serializer.data},
            status=201,
        )
 
 
class CompanyInvitationListView(APIView):
    """
    Returns all company invitations (platform-admin only).
    Ordered by most-recently created first.
    """
    permission_classes = [IsAuthenticated]
 
    def get(self, request):
        if request.user.role != "platform_admin":
            return Response(
                {"error": "Only platform admins can view invitations."},
                status=403,
            )
 
        invitations = CompanyInvitation.objects.all().order_by("-created_at")
        serializer = CompanyInvitationSerializer(invitations, many=True)
        return Response(serializer.data)
 
 
class CompanyInvitationDetailView(APIView):
    """
 
    Public endpoint used during the registration flow to validate an
    invitation token before the new admin fills in their details.
 
    Returns 400 if the invitation is expired or has already been used/
    cancelled.  Returns the company pre-fill data on success so the
    Register page can lock those fields.
    """
    permission_classes = [AllowAny]
 
    def get(self, request, token):
        invitation = get_object_or_404(CompanyInvitation, token=token)
 
        if invitation.expires_at and invitation.expires_at < timezone.now():
            return Response({"error": "This invitation has expired."}, status=400)
 
        if invitation.status != "pending":
            return Response(
                {"error": "This invitation has already been used or cancelled."},
                status=400,
            )
 
        return Response({
            "email": invitation.email,
            "company_name": invitation.company_name,
            "company_slug": invitation.company_slug,
            "is_valid": True,
        })
 
 
class CompanyInvitationCancelView(APIView):
    """

    Platform-admin-only endpoint to cancel a pending invitation by its
    token (string).  Using the token (not the PK) keeps the frontend
    consistent — it stores and references invitations by token.
 
    Returns 200 {"message": "Invitation cancelled"} on success.
    Returns 400 if the invitation is not in a cancellable state.
    """
    permission_classes = [IsAuthenticated]
 
    def post(self, request, token):
        if request.user.role != "platform_admin":
            return Response(
                {"error": "Only platform admins can cancel invitations."},
                status=403,
            )
 
        invitation = get_object_or_404(CompanyInvitation, token=token)
 
        if invitation.status != "pending":
            return Response(
                {"error": "Only pending invitations can be cancelled."},
                status=400,
            )
 
        invitation.status = CompanyInvitation.STATUS_CANCELLED
        invitation.save(update_fields=["status"])
 
        return Response({"message": "Invitation cancelled", "token": str(token)})
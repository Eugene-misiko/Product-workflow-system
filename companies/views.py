"""
Company management views including:
- Company details and settings
- Dashboard statistics
- Staff management
"""
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count
from django.utils import timezone
from .models import Company, CompanySettings, CompanyInvitation
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


class CompanyUpdateView(generics.UpdateAPIView):
    """
    Update company details (admin only).
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CompanyUpdateSerializer
    
    def get_object(self):
        if not self.request.user.is_company_admin:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only company admin can update company details.")
        return self.request.user.company

class CompanySettingsView(generics.RetrieveUpdateAPIView):
    """
    Get or update company settings (admin only).
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CompanySettingsSerializer
    
    def get_object(self):
        if not self.request.user.is_company_admin:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only company admin can manage settings.")
        
        company = self.request.user.company
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
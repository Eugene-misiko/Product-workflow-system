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
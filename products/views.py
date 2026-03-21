"""
Product management views:
- Public: Browse products and categories
- Admin: CRUD operations for products
"""
from django.shortcuts import render
from rest_framework import status, generics, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from .models import Category, Product, ProductField
from .serializers import (
    CategorySerializer, CategoryDetailSerializer,
    ProductSerializer, ProductListSerializer, CreateProductSerializer,
    ProductFieldSerializer
)
from accounts.models import User
# Create your views here.


# CATEGORY VIEWS
class CategoryListView(generics.ListAPIView):
    """
    List categories for current company.
    
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CategorySerializer
    
    def get_queryset(self):
        return Category.objects.filter(
            company=self.request.user.company,
            is_active=True
        ).order_by('order', 'name')

#category detail view
class CategoryDetailView(generics.RetrieveAPIView):
    """
    Get category with products.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CategoryDetailSerializer
    
    def get_queryset(self):
        return Category.objects.filter(company=self.request.user.company)
class CreateCategoryView(generics.CreateAPIView):
    """
    Create category (admin only).
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CategorySerializer
    
    def perform_create(self, serializer):
        if not self.request.user.is_company_admin:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only admin can create categories.")
        serializer.save(company=self.request.user.company)

class UpdateCategoryView(generics.UpdateAPIView):
    """
    Update category (admin only).
    PUT/PATCH /api/categories/{pk}/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CategorySerializer
    
    def get_queryset(self):
        if not self.request.user.is_company_admin:
            return Category.objects.none()
        return Category.objects.filter(company=self.request.user.company)
        
class DeleteCategoryView(generics.DestroyAPIView):
    """
    Delete category (admin only).

    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if not self.request.user.is_company_admin:
            return Category.objects.none()
        return Category.objects.filter(company=self.request.user.company)

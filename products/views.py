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
from rest_framework.parsers import MultiPartParser, FormParser,JSONParser
from django.shortcuts import get_object_or_404
from .models import Category, Product, ProductField
from .serializers import (
    CategorySerializer,
    CategoryDetailSerializer,
    ProductSerializer, ProductListSerializer, CreateProductSerializer,
    ProductFieldSerializer
)
from accounts.models import User
from rest_framework.exceptions import PermissionDenied
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
        ).prefetch_related('products').order_by('order', 'name')

#category detail view
class CategoryDetailView(generics.RetrieveAPIView):
    """
    Get category with products.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CategoryDetailSerializer
    
    def get_queryset(self):
        return Category.objects.filter(company=self.request.user.company, is_active=True)
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
    def perform_update(self, serializer):
        serializer.save()
class DeleteCategoryView(generics.DestroyAPIView):
    """
    Delete category (admin only).

    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if not self.request.user.is_company_admin:
            return Category.objects.none()
        return Category.objects.filter(company=self.request.user.company)

# =====================
# PRODUCT VIEWS
# =====================

class ProductListView(generics.ListAPIView):
    """
    List products for current company.
    
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ProductListSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'is_featured', 'requires_design']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'price', 'created_at']
    
    def get_queryset(self):
        queryset = Product.objects.filter(
            company=self.request.user.company,
            is_active=True
        ).select_related('category')
        
        if not self.request.user.is_company_admin:
            queryset = queryset.filter(is_active=True)
        return queryset.order_by('-is_featured', '-created_at')

class ProductDetailView(generics.RetrieveAPIView):
    """
    Get product details.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.filter(company=self.request.user.company)

        if not self.request.user.is_company_admin:
            queryset = queryset.filter(is_active=True)
        
        return queryset


class CreateProductView(generics.CreateAPIView):
    """
    Create product (admin only).
    
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = [IsAuthenticated]
    serializer_class = CreateProductSerializer
    def perform_create(self, serializer):
        if not self.request.user.is_company_admin:
            
            raise PermissionDenied("Only admin can create products.")
        serializer.save()


class UpdateProductView(generics.UpdateAPIView):
    """
    Update product (admin only).
    
    PUT/PATCH /api/products/{pk}/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CreateProductSerializer
    
    def get_queryset(self):
        if not self.request.user.is_company_admin:
            return Product.objects.none()
        return Product.objects.filter(company=self.request.user.company)

    def perform_update(self, serializer):
        serializer.save()

class DeleteProductView(generics.DestroyAPIView):
    """
    Delete product (admin only) - Soft delete.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if not self.request.user.is_company_admin:
            return Product.objects.none()
        return Product.objects.filter(company=self.request.user.company)
    
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

class FeaturedProductsView(generics.ListAPIView):
    """
    Get featured products.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ProductListSerializer
    
    def get_queryset(self):
        return Product.objects.filter(
            company=self.request.user.company,
            is_featured=True,
            is_active=True
        ).order_by('-created_at')


# =====================
# PUBLIC VIEWS (No Auth)
# =====================

class PublicProductListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProductListSerializer

    def get_queryset(self):
        company_slug = self.request.query_params.get("company")

        if not company_slug:
            return Product.objects.none()

        return Product.objects.filter(
            company__slug=company_slug,
            is_active=True
        ).select_related("category")


class PublicCategoryListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CategorySerializer

    def get_queryset(self):
        company_slug = self.request.query_params.get('company')

        if not company_slug:
            return Category.objects.none()

        return Category.objects.filter(
            company__slug=company_slug,
            is_active=True
        ).order_by('name')

class PublicProductDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProductSerializer

    def get_queryset(self):
        company_slug = self.request.query_params.get("company")

        if not company_slug:
            return Product.objects.none()

        return Product.objects.filter(
            company__slug=company_slug,
            is_active=True
        )
class PublicCategoryDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = CategoryDetailSerializer

    def get_queryset(self):
        company_slug = self.request.query_params.get("company")

        if not company_slug:
            return Category.objects.none()

        return Category.objects.filter(
            company__slug=company_slug,
            is_active=True
        )       




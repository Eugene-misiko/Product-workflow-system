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
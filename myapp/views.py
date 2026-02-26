from rest_framework.viewsets import ModelViewSet
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer
from accounts.permissions import IsAdmin
from accounts.models import User 
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from .models import Subscriber ,ItemOrder
from .forms import CategoryForm, ProductForm
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, permissions
from .serializers import ItemOrderSerializer
from .permissions import IsAdminOrOwner
# create your views here
class CategoryViewSet(ModelViewSet):
    """Admin manages categories"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdmin]

class ProductViewSet(ModelViewSet):
    """Admin manages products"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdmin]
    
#this is the template views for backend 
#modifying---1
def product_list(request, category_slug=None):
    category = None
    """
    Admin-only: Display all products in a table.
    """
    if not request.user.is_authenticated or request.user.role != "client":
        return render(request, "forbidden.html", status=403)
    products = Product.objects.filter(available=True)
    categories = Category.objects.all()
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    return render(request, "product_list.html", {
        "products": products, 
        "category": category, 
        "categories": categories})
#creating the product detail---2
def product_detail(request, id, slug):
    product = get_object_or_404(Product, id=id, slug=slug, available=True)
    return render(request, 'detail.html', {"product":product})#I will change to detail.html

  
#The combination products
class ItemOrderViewSet(viewsets.ModelViewSet):
    serializer_class = ItemOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return ItemOrder.objects.all()
        return ItemOrder.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


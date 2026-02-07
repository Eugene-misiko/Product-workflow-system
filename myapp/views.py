from rest_framework.viewsets import ModelViewSet
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer
from accounts.permissions import IsAdmin
from accounts.models import User
from django.shortcuts import render

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
def category_list_template(request):
    """
    Admin-only: Display all categories in a table.
    """
    if not request.user.is_authenticated or request.user.role != "admin":
        return render(request, "forbidden.html", status=403)

    categories = Category.objects.all()
    return render(request, "category_list.html", {"categories": categories})

def product_list_template(request):
    """
    Admin-only: Display all products in a table.
    """
    if not request.user.is_authenticated or request.user.role != "admin":
        return render(request, "forbidden.html", status=403)

    products = Product.objects.all()
    return render(request, "product_list.html", {"products": products})
 

        
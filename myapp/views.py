from rest_framework.viewsets import ModelViewSet
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer
from users.permissions import IsAdmin

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
    

 

        
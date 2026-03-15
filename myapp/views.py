from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .models import Product, Category
from .serializers import ProductSerializer, CategorySerializer
from .permissions import IsAdmin


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing products.
    - Anyone can view products
    - Only admin can create, update, delete
    """

    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdmin()]
        return [AllowAny()]
        
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer        


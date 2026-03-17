from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .models import Product, Category, ProductField
from .serializers import ProductSerializer, CategorySerializer,ProductFieldSerializer
from rest_framework.response import Response
from rest_framework.decorators import action
from .permissions import IsAdmin

class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing products.
    - Anyone can view products
    - Only admin can create, update, delete
    """

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    @action(detail=True, methods=["get"])
    def fields(self, request, pk=None):
        product = self.get_object()
        fields = product.fields.all()
        serializer = ProductFieldSerializer(fields, many=True)
        return Response(serializer.data)
        
    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdmin()]
        return [AllowAny()]

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer 

class ProductFieldViewSet(viewsets.ModelViewSet):
    queryset = ProductField.objects.all()
    serializer_class = ProductFieldSerializer           


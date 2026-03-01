from rest_framework import generics
from rest_framework.permissions import AllowAny
from .models import Product
from .serializers import ProductSerializer
from .permissions import IsAdmin

class ProductListView(generics.ListCreateAPIView):
    """
    List all active products.
    Admin can create new products.
    """

    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdmin()]
        return [AllowAny()]


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve a product.
    Admin can update or delete.
    """

    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsAdmin()]
        return [AllowAny()]
from rest_framework import serializers
from .models import Order

class OrderSerializer(serializers.ModelSerializer):

    product_name = serializers.CharField(source="product.name", read_only=True)
    design_file = serializers.ImageField(read_only=True)
    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "product",
            "product_name",
            "quantity",
            "needs_design",        
            "design_file",
            "description",         
            "status",
            "assigned_designer",
            "rejection_reason",
            "created_at",
        ]
        read_only_fields = (
            "user",
            "status",
            "rejection_reason",
            "assigned_designer",
        )
    def get_design_file(self, obj):
        if obj.design_file:
            return obj.design_file.url
        return None        
from rest_framework import serializers
from .models import Order, OrderItem, OrderItemFieldValue, OrderStatusHistory, PrintJob, Transportation


class OrderItemFieldValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItemFieldValue
        fields = ['id', 'field', 'value', 'file_url']


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    field_values = OrderItemFieldValueSerializer(many=True, read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_name', 'quantity',
            'unit_price', 'subtotal', 'specifications', 'notes',
            'field_values', 'created_at'
        ]
        read_only_fields = ['id', 'unit_price', 'subtotal', 'created_at']
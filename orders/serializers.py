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


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)
    
    class Meta:
        model = OrderStatusHistory
        fields = ['id', 'old_status', 'new_status', 'changed_by', 'changed_by_name', 'note', 'created_at']
        read_only_fields = ['id', 'created_at']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    designer_name = serializers.CharField(source='assigned_designer.get_full_name', read_only=True)
    printer_name = serializers.CharField(source='assigned_printer.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'user_name',
            'assigned_designer', 'designer_name',
            'assigned_printer', 'printer_name',
            'status', 'status_display', 'priority',
            'subtotal', 'tax', 'delivery_fee', 'discount', 'total_price',
            'needs_design', 'design_description',
            'created_at', 'updated_at', 'items'
        ]
        read_only_fields = ['id', 'order_number', 'subtotal', 'total_price', 'created_at', 'updated_at']


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'user_name',
            'assigned_designer', 'assigned_printer',
            'status', 'priority',
            'subtotal', 'tax', 'delivery_fee', 'discount', 'total_price',
            'needs_design', 'design_file', 'design_description', 'design_notes',
            'design_revisions', 'max_revisions',
            'client_files', 'description', 'internal_notes',
            'rejection_reason', 'cancellation_reason',
            'design_started_at', 'design_completed_at',
            'printing_started_at', 'printing_completed_at',
            'completed_at', 'estimated_completion',
            'created_at', 'updated_at',
            'items', 'status_history',
        ]



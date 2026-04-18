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
    design_file_url = serializers.SerializerMethodField()
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'user_name',
            'assigned_designer', 'designer_name','design_file_url',
            'assigned_printer', 'printer_name',
            'status', 'status_display', 'priority',
            'subtotal', 'tax', 'delivery_fee', 'discount', 'total_price',
            'needs_design', 'design_description',
            'created_at', 'updated_at', 'items','design_file','design_file_url'
        ]
        read_only_fields = ['id', 'order_number', 'subtotal', 'total_price', 'created_at', 'updated_at']
    def get_design_file_url(self, obj):
        if obj.design_file:
            return obj.design_file.url
        return None

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

class CreateOrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    
    class Meta:
        model = Order
        fields = [
            'items', 'needs_design', 'design_description',
            'client_files', 'description', 'priority'
        ]
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        order = Order.objects.create(**validated_data)
        
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
            #added new outcome
        if validated_data.get('client_files') or validated_data.get('design_file'):
            validated_data['needs_design'] = False
        else:
            validated_data['needs_design'] = True        
        OrderStatusHistory.objects.create(
            order=order,
            old_status='',
            new_status=Order.STATUS_PENDING,
            note='Order created'
        )
        
        return order


class AssignDesignerSerializer(serializers.Serializer):
    designer_id = serializers.IntegerField()

class AssignPrinterSerializer(serializers.Serializer):
    printer_id = serializers.IntegerField()


class SubmitDesignSerializer(serializers.Serializer):
    design_file = serializers.FileField(required=False)
    design_notes = serializers.CharField(required=False, allow_blank=True)

class ApproveDesignSerializer(serializers.Serializer):
    approved = serializers.BooleanField()
    rejection_reason = serializers.CharField(required=False, allow_blank=True)


class PrintJobSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    assigned_printer_name = serializers.CharField(source='assigned_printer.get_full_name', read_only=True)
    
    class Meta:
        model = PrintJob
        fields = [
            'id', 'order', 'order_number',
            'assigned_printer', 'assigned_printer_name',
            'status', 'print_quantity', 'paper_type', 'print_color', 'finish_type',
            'progress_percentage', 'print_notes', 'issues',
            'started_at', 'estimated_completion', 'completed_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TransportationSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = Transportation
        fields = [
            'id', 'order', 'order_number',
            'transport_type', 'status',
            'delivery_address', 'delivery_city', 'delivery_phone', 'delivery_instructions',
            'pickup_location', 'pickup_scheduled_time',
            'delivery_scheduled_time', 'estimated_arrival', 'actual_delivery_time',
            'tracking_number', 'tracking_url', 'driver_name', 'driver_phone',
            'delivery_fee', 'notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CreateTransportationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transportation
        fields = [
            'transport_type',
            'delivery_address', 'delivery_city', 'delivery_phone', 'delivery_instructions',
            'pickup_scheduled_time', 'delivery_scheduled_time',
            'notes'
        ]


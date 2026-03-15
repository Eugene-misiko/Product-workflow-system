from rest_framework import serializers
from .models import Order, Invoice, OrderItem, OrderItemField


class OrderItemFieldSerializer(serializers.ModelSerializer):
    field_name = serializers.CharField(source="field.name", read_only=True)

    class Meta:
        model = OrderItemField
        fields = ["field_name", "value"]


class OrderItemSerializer(serializers.ModelSerializer):

    product_name = serializers.CharField(source="product.name", read_only=True)
    product_price = serializers.DecimalField(
        source="product.price",
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    product_image = serializers.ImageField(source="product.image", read_only=True)

    fields = OrderItemFieldSerializer(
        source="field_values",
        many=True,
        read_only=True
    )

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "product_name",
            "product_price",
            "product_image",
            "quantity",
            "unit_price",
            "subtotal",
            "fields",
        ]


class OrderSerializer(serializers.ModelSerializer):

    order_number = serializers.CharField(read_only=True)

    invoice_id = serializers.SerializerMethodField()

    items = OrderItemSerializer(many=True, read_only=True)

    design_file = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "user",
            "needs_design",
            "design_file",
            "description",
            "status",
            "rejection_reason",
            "total_price",
            "items",
            "created_at",
            "invoice_id",
        ]

        read_only_fields = (
            "user",
            "status",
            "rejection_reason",
            "total_price",
        )

    def get_design_file(self, obj):
        if obj.design_file:
            return obj.design_file.url
        return None

    def get_invoice_id(self, obj):
        if hasattr(obj, "invoice"):
            return obj.invoice.id
        return None


class InvoiceSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()
    unit_price = serializers.SerializerMethodField()
    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "product_name",
            "quantity",
            "unit_price",
            "total_amount",
            "deposit_amount",
            "balance_due",
            "status",
            "created_at",
        ]

    def get_product_name(self, obj):
        item = obj.order.items.first()
        return item.product.name if item else None
    def get_quantity(self, obj):
        item = obj.order.items.first()
        return item.quantity if item else None

    def get_unit_price(self, obj):
        item = obj.order.items.first()
        return item.product.price if item else None
from rest_framework import serializers
from .models import Order,Invoice

class OrderSerializer(serializers.ModelSerializer):
    invoice_id = serializers.SerializerMethodField()
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_price = serializers.DecimalField(
        source="product.price",
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    product_image = serializers.ImageField(source="product.image", read_only=True)

    total_price = serializers.SerializerMethodField()
    design_file = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "product",
            "product_name",
            "product_price",
            "product_image",
            "quantity",
            "needs_design",
            "design_file",
            "description",
            "status",
            "rejection_reason",
            "total_price",
            "created_at",
            "invoice_id",
        ]
        read_only_fields = ("user", "status", "rejection_reason")

    def get_total_price(self, obj):
        return obj.product.price * obj.quantity

    def get_design_file(self, obj):
        if obj.design_file:
            return obj.design_file.url
        return None
    def get_invoice_id(self, obj):
        if hasattr(obj, "invoice"):
            return obj.invoice.id
        return None
    
class InvoiceSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="order.product.name",read_only=True)
    quantity = serializers.IntegerField(source="order.quantity",read_only=True)
    unit_price = serializers.DecimalField(source="order.product.price",max_digits=10,decimal_places=2,read_only=True)
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


from rest_framework import serializers
from .models import Category, Product, Item_order
from .utils import PRODUCT_MODELS
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"


class DynamicOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item_order
        fields = ['id', 'product_type', 'product_id', 'quantity', 'status', 'created_at']
        read_only_fields = ['status', 'created_at', 'user']

    def validate(self, attrs):
        product_type = attrs.get('product_type').lower()
        product_id = attrs.get('product_id')
        quantity = attrs.get('quantity', 1)

        if product_type not in PRODUCT_MODELS:
            raise serializers.ValidationError({'product_type': 'Invalid product type'})

        product_model = PRODUCT_MODELS[product_type]
        try:
            product = product_model.objects.get(id=product_id)
        except product_model.DoesNotExist:
            raise serializers.ValidationError({'product_id': 'Product does not exist'})

        if quantity > product.quantity_available:
            raise serializers.ValidationError({'quantity': 'Not enough stock available'})

        attrs['product_instance'] = product
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        product = validated_data.pop('product_instance')
        quantity = validated_data['quantity']

        product.quantity_available -= quantity
        product.save()

        order = Item_order.objects.create(
            user=user,
            product_type=validated_data['product_type'],
            product_id=validated_data['product_id'],
            quantity=quantity
        )
        return order
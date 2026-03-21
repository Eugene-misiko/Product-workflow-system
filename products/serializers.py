from rest_framework import serializers
from .models import Category, Product, ProductField

class ProductFieldSerializer(serializers.ModelSerializer):
    """Product custom field serializer."""
    
    class Meta:
        model = ProductField
        fields = [
            'id', 'name', 'field_type', 'required',
            'options', 'placeholder', 'help_text', 'order'
        ]


class CategorySerializer(serializers.ModelSerializer):
    """Category serializer."""
    
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'image',
            'is_active', 'order', 'products_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
    
    def get_products_count(self, obj):
        return obj.products.filter(is_active=True).count()

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
    def validate_category(self, value):
        request = self.context.get('request')
        company = request.user.company

        if value.company != company:
            raise serializers.ValidationError("Invalid category for this company.")
        
        return value   

    def get_products_count(self, obj):
        return obj.products.filter(is_active=True).count()
    
class CategoryDetailSerializer(serializers.ModelSerializer):
    """Category with products."""
    
    products = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'image',
            'is_active', 'order', 'products',
            'created_at', 'updated_at'
        ]
    
    def get_products(self, obj):
        request = self.context.get('request')
        company = request.user.company
        products = obj.products.filter(is_active=True,company=company)

        return ProductListSerializer(products, many=True).data


class ProductListSerializer(serializers.ModelSerializer):
    """Product list serializer (lightweight)."""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    price_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'price', 'price_display',
            'category_name', 'image', 'is_featured',
            'production_time', 'is_active'
        ]
    
    def get_price_display(self, obj):
        return f"KSh {obj.price:,.2f}"

class ProductSerializer(serializers.ModelSerializer):
    """Product serializer."""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    price_display = serializers.SerializerMethodField()
    fields = ProductFieldSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'price_display',
            'category', 'category_name',
            'image', 'gallery',
            'min_quantity', 'max_quantity',
            'requires_design', 'design_templates',
            'production_time', 'print_specs',
            'is_active', 'is_featured',
            'fields',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
    
    def get_price_display(self, obj):
        return f"KSh {obj.price:,.2f}"
class CreateProductSerializer(serializers.ModelSerializer):
    """Create product serializer (admin only)."""
    
    fields = ProductFieldSerializer(many=True, required=False)
    
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'price',
            'category', 'image',
            'min_quantity', 'max_quantity',
            'requires_design', 'production_time',
            'has_quantity_pricing', 'quantity_pricing',
            'print_specs', 'fields'
        ]
    def validate_quantity_pricing(self, value):
        for tier in value:
            if 'min_qty' not in tier or 'price' not in tier:
                raise serializers.ValidationError("Invalid quantity pricing format.")
        return value
            
    def create(self, validated_data):
        fields_data = validated_data.pop('fields', [])
        request = self.context.get('request')
        company = request.user.company 
        product = Product.objects.create(company=company, **validated_data)
        for field_data in fields_data:
            ProductField.objects.create(
                product=product,
                company=company,
                **field_data
            )
        
        return product
    
    def update(self, instance, validated_data):
        fields_data = validated_data.pop('fields', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if fields_data is not None:
            instance.fields.all().delete()
            for field_data in fields_data:
                ProductField.objects.create(product=instance,company=instance.company, **field_data)
        
        return instance

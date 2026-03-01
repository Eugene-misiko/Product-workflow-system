from rest_framework import serializers
from .models import Category, Product, ItemOrder
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"

class ProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = "__all__"

class ItemOrderSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)    

    class Meta:
        model = ItemOrder
        fields = '__all__'
        read_only_fields = ['user', 'status', 'created_at']

from rest_framework import serializers

from .models import Book

class BookSerializer(serializers.ModelSerializer):
    title = serializers.CharField(max_length=150)
    author = serializers.CharField(max_length=100)
    description = serializers.CharField()
    publisher = serializers.CharField(max_length=100)
    published_date = serializers.DateField(required=False)
    page_count = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    price = serializers.DecimalField(max_digits=6, decimal_places=2, allow_null=True, required=False)
    updated_at = serializers.DateTimeField(read_only=True) 


    class Meta:
        model = Book

        fields = '__all__'   
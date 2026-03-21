from rest_framework import serializers
from .models import Company, CompanySettings, CompanyInvitation

class CompanySerializer(serializers.ModelSerializer):
    """Basic company serializer."""
    
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'slug', 'code', 'logo',
            'email', 'phone', 'address', 'city', 'country', 'website',
            'currency', 'currency_symbol',
            'is_active', 'subscription_plan',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'code', 'created_at', 'updated_at']

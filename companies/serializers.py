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

class CompanyDetailSerializer(serializers.ModelSerializer):
    """Detailed company serializer with settings."""
    
    settings = serializers.SerializerMethodField()
    staff_count = serializers.IntegerField(read_only=True)
    clients_count = serializers.IntegerField(read_only=True)
    orders_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'slug', 'code', 'logo',
            'email', 'phone', 'address', 'city', 'country', 'website',
            'custom_domain', 'subdomain',
            'currency', 'currency_symbol', 'deposit_percentage',
            'is_active', 'subscription_plan',
            'staff_count', 'clients_count', 'orders_count',
            'settings',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'code', 'created_at', 'updated_at']
    
    def get_settings(self, obj):
        try:
            settings = obj.settings
            return {
                'working_days': settings.working_days,
                'opening_time': str(settings.opening_time) if settings.opening_time else None,
                'closing_time': str(settings.closing_time) if settings.closing_time else None,
                'accept_mpesa': settings.accept_mpesa,
                'accept_cash': settings.accept_cash,
                'offer_delivery': settings.offer_delivery,
                'delivery_fee': str(settings.delivery_fee),
                'whatsapp_number': settings.whatsapp_number,
            }
        except CompanySettings.DoesNotExist:
            return None
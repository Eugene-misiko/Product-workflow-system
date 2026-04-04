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


class CompanySettingsSerializer(serializers.ModelSerializer):
    """Company settings serializer."""
    
    class Meta:
        model = CompanySettings
        fields = [
            'working_days', 'opening_time', 'closing_time', 'timezone',
            'email_notifications', 'sms_notifications',
            'accept_mpesa', 'accept_cash', 'accept_card', 'accept_bank_transfer',
            'mpesa_shortcode', 'mpesa_passkey',
            'mpesa_consumer_key', 'mpesa_consumer_secret',
            'offer_pickup', 'offer_delivery',
            'delivery_fee', 'free_delivery_threshold',
            'facebook', 'instagram', 'twitter', 'whatsapp_number',
            'terms_conditions', 'privacy_policy',
        ]

class CompanyUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating company info."""
    
    class Meta:
        model = Company
        fields = [
            'name', 'logo', 'phone', 'address', 'city', 'country', 'website',
            'currency', 'currency_symbol', 'deposit_percentage','email'
        ]


class CompanyInvitationSerializer(serializers.ModelSerializer):
    """Company invitation serializer."""
    
    invited_by_name = serializers.CharField(source='invited_by.get_full_name', read_only=True)
    
    class Meta:
        model = CompanyInvitation
        fields = [
            'id', 'token', 'email', 'company_name',
            'invited_by', 'invited_by_name',
            'status', 'company',
            'created_at', 'expires_at', 'accepted_at'
        ]
        read_only_fields = ['id', 'token', 'invited_by', 'status', 'company', 'created_at', 'expires_at', 'accepted_at']

class DashboardStatsSerializer(serializers.Serializer):
    """Dashboard statistics serializer."""
    
    total_orders = serializers.IntegerField()
    pending_orders = serializers.IntegerField()
    completed_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    pending_payments = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_clients = serializers.IntegerField()
    total_staff = serializers.IntegerField()
    recent_orders = serializers.ListField()
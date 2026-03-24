from rest_framework import serializers
from .models import Invoice, MpesaRequest, MpesaResponse, Payment, Receipt

# ----------------------------
# Invoice Serializer (read-only fields ok)
# ----------------------------
class InvoiceSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    client_name = serializers.CharField(source='order.user.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_deposit_paid = serializers.BooleanField(read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'order', 'order_number',
            'client_name',
            'subtotal', 'tax', 'delivery_fee', 'discount', 'total_amount',
            'deposit_percentage', 'deposit_amount', 'deposit_paid',
            'balance_due', 'amount_paid',
            'status', 'status_display',
            'issue_date', 'due_date',
            'is_deposit_paid',
            'created_at', 'updated_at'
        ]


# MpesaRequest Serializer

class MpesaRequestSerializer(serializers.ModelSerializer):
    # Auto-set user from request
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = MpesaRequest
        fields = '__all__'

    def validate_invoice(self, value):
        user_company = self.context['request'].user.company
        if value.company != user_company:
            raise serializers.ValidationError("Invoice does not belong to your company.")
        return value

# MpesaResponse Serializer

class MpesaResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = MpesaResponse
        fields = '__all__'


# Payment Serializer
class PaymentSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    payment_type_display = serializers.CharField(source='get_payment_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    recorded_by = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Payment
        fields = [
            'id', 'payment_number', 'invoice', 'invoice_number',
            'payment_type', 'payment_type_display',
            'amount', 'payment_method',
            'status', 'status_display',
            'transaction_id',
            'recorded_by',
            'created_at', 'completed_at'
        ]

    def validate_invoice(self, value):
        user_company = self.context['request'].user.company
        if value.company != user_company:
            raise serializers.ValidationError("Invoice does not belong to your company.")
        return value


# Create Payment Serializer

class CreatePaymentSerializer(serializers.Serializer):
    invoice_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_type = serializers.ChoiceField(choices=['deposit', 'balance', 'full'])
    payment_method = serializers.ChoiceField(choices=['mpesa', 'cash', 'card'])
    transaction_id = serializers.CharField(required=False, default='')
    notes = serializers.CharField(required=False, default='')

    def validate_invoice_id(self, value):
        user_company = self.context['request'].user.company
        try:
            invoice = Invoice.objects.get(id=value, company=user_company)
        except Invoice.DoesNotExist:
            raise serializers.ValidationError("Invoice not found in your company.")
        return value


# Receipt Serializer
class ReceiptSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)

    class Meta:
        model = Receipt
        fields = [
            'id', 'receipt_number',
            'order', 'order_number',
            'invoice', 'payment',
            'mpesa_receipt', 'amount_paid', 'payment_type',
            'created_at'
        ]

# STK Push Serializer

class StkPushSerializer(serializers.Serializer):
    invoice_id = serializers.IntegerField()
    phone_number = serializers.CharField(max_length=15)

    def validate_phone_number(self, value):
        if not value.startswith('254') or len(value) != 12:
            raise serializers.ValidationError('Phone must be format: 2547XXXXXXXX')
        return value

    def validate_invoice_id(self, value):
        user_company = self.context['request'].user.company
        try:
            invoice = Invoice.objects.get(id=value, company=user_company)
        except Invoice.DoesNotExist:
            raise serializers.ValidationError("Invoice not found in your company.")
        return value
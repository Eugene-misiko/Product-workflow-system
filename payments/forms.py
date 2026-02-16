from django import forms
from .models import Payment, MethodPay

class PaymentForm(forms.ModelForm):
    phone_number = forms.CharField(
        max_length=15, 
        required=True,
        label="Phone Number"
    )

    class Meta:
        model = Payment
        fields = ["method_of_payment", "amount", "phone_number"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make method_of_payment a dropdown with choices
        self.fields['method_of_payment'].queryset = MethodPay.objects.all()

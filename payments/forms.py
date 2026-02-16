from django import forms
from .models import Payment

class PaymentForm(forms.ModelForm):
    """
    Payment creation form including phone number for MPESA STK Push.
    """
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        label="Phone Number",
        widget=forms.TextInput(attrs={"placeholder": "2547XXXXXXXX"})
    )

    class Meta:
        model = Payment
        fields = ["method_of_payment", "amount", "phone_number"]


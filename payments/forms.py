from django import forms
from .models import Payment



class PaymentForm(forms.ModelForm):
    """
    Payment creation form.
    """

    class Meta:
        model = Payment
        fields = ["method_of_payment", "amount"]# amount

        



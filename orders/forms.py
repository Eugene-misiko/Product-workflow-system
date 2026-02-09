from django import forms

from .models import Order

class OrderForm(forms.ModelForm):
    """
        Order creation/edit form
    """
    class Meta:
        model = Order
        fields = []
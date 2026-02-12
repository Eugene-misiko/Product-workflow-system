from django import forms

from .models import Order,OrderItem,Product

class OrderForm(forms.ModelForm):
    """
        Order creation/edit form
    """
    class Meta:
        model = Order #Product
        fields = '__all__'
 
class Item(forms.ModelForm):
    """
    creating Item form
    """

    class Meta:
        model = OrderItem
        fields = "__all__"

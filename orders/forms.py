from django import forms

from .models import Order,OrderItem,Product, OrderCreateForm
from myapp.models import Category
#modified 
class OrderCreationForm(forms.ModelForm):
    """
    creating the fields for the order creation form
    """

    class Meta:
        model =OrderCreateForm
        exclude = ['client']

class Item(forms.ModelForm):
    """
    creating Item form
    """

    class Meta:
        model = OrderItem
        fields = '__all__'

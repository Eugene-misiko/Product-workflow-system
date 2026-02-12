from django import forms

from .models import Order,OrderItem,Product
from myapp.models import Category
#modified 
class OrderCreateForm(forms.Form):
    """
    Form used by client to create an order.

    Flow:
    1. Select category
    2. Select product (filtered by category)
    3. Enter quantity
    """

    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        empty_label="Select category"
    )

    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_active=True),
        empty_label="Select product"
    )

    quantity = forms.IntegerField(min_value=1)

class Item(forms.ModelForm):
    """
    creating Item form
    """

    class Meta:
        model = OrderItem
        fields = '__all__'

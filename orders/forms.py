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

class OrderCreateForm(forms.ModelForm):
    category = forms.ModelChoiceField(queryset=Category.objects.filter(is_active=True), required=True)
    product = forms.ModelChoiceField(queryset=Product.objects.none(), required=True)
    quantity = forms.IntegerField(min_value=1, required=True)
    color = forms.CharField(max_length=50, required=True)

    class Meta:
        model = OrderItem
        fields = ['category', 'product', 'quantity', 'color']

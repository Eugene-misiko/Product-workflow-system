from django import forms

from .models import Order,OrderItem,Product
from myapp.models import Category
#modified 

DESIGN_CHOICES = [
    ("designed", "I have my design"),
    ("not_designed", "I want it designed"),
]

PAPER_CHOICES = [
    ("matte", "Matte"),
    ("glossy", "Glossy"),
]

EDIT_CHOICES = [
    ("simple", "Simple editing"),
    ("full", "Full editing"),
]
class OrderCreateForm(forms.Form):
    """
    Form used by client to create an order.

    Flow:
    1. Select category
    2. Select product (filtered by category)
    3. Enter quantity
    """
    category = forms.ModelChoiceField(queryset=Category.objects.filter(is_active=True),required=True)
    product = forms.ModelChoiceField(queryset=Product.objects.none(),required=False)
    quantity = forms.IntegerField(min_value=1,required=True)
    color_type = forms.CharField(max_length=50,required=False)
    design_type = forms.ChoiceField(choices=DESIGN_CHOICES,required=False)
    description = forms.CharField(widget=forms.Textarea,required=False)
    paper_type = forms.ChoiceField(choices=PAPER_CHOICES,required=False)
    editing_type = forms.ChoiceField(choices=EDIT_CHOICES,required=False)




class Item(forms.ModelForm):
    """
    creating Item form
    """

    class Meta:
        model = OrderItem
        fields = '__all__'

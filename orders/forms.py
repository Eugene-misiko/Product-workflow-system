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
    name = forms.CharField(max_length=150)
    category_code = forms.CharField(required=True,initial=1 )
    quantity = forms.IntegerField(min_value=1,required=True)
    color_mode = forms.CharField(max_length=50,required=False)
    design_type = forms.ChoiceField(choices=DESIGN_CHOICES,required=False)
    description = forms.CharField(widget=forms.Textarea,required=False)
    paper_type = forms.ChoiceField(choices=PAPER_CHOICES,required=False)
    editing_type = forms.ChoiceField(choices=EDIT_CHOICES,required=False)
    paper_size = forms.CharField(max_length=50, required=False)
    number_of_pages = forms.IntegerField(min_value=1, required=True)
    has_spine = forms.BooleanField(initial=False)
    spine_size_mm =forms.FloatField(required=True)
    binding_type= forms.ChoiceField( required=True,
        choices=[
            ('perfect', 'Perfect Binding'),
            ('spiral', 'Spiral Binding'),
            ('hardcover', 'Hardcover'),
            ('stapled', 'Stapled'),
        ])
    # Apparel specific
    size = forms.CharField(max_length=20, required=True)
    material = forms.CharField(max_length=100, required=False)
    # Plate specific
    plate_diameter_cm = forms.FloatField(required=False)
    # Upload design file
    design_file = forms.FileField(required=True)
    



class Item(forms.ModelForm):
    """
    creating Item form
    """

    class Meta:
        model = OrderItem
        fields = '__all__'

from django import forms

from .models import Order,OrderItem,Product,OrderItemSpecification
from myapp.models import Category
#modified 

DESIGN_CHOICES = [
    ("designed", "I have my design"),
    ("not_designed", "I want it designed"),
]

PAPER_CHOICES = [
    ("matte", "Matte"),
    ("glossy", "Glossy"),
    ('book_paper', 'Book Paper'),
]

COVER_CHOICES = [
    ("matte", "Matte"),
    ("glossy", "Glossy"),
]

EDIT_CHOICES = [
    ("simple", "Simple editing"),
    ("full", "Full editing"),
]

BINDING_CHOICES = [
    ('perfect', 'Perfect Binding'),
    ('spiral', 'Spiral Binding'),
    ('hardcover', 'Hardcover'),
    ('stapled', 'Stapled'),
]

class OrderCreateForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.none(),
        empty_label="-- Choose a product --",
        required=True
    )
    quantity = forms.IntegerField(min_value=1, required=True)
    color_type = forms.CharField(max_length=50, required=False)
    design_type = forms.ChoiceField(
        choices=[("designed", "I have my design"), ("not_designed", "I want it designed")],
        required=False
    )
    description = forms.CharField(widget=forms.Textarea, required=False)

    # Book / paper fields
    number_of_pages = forms.IntegerField(min_value=1, required=False)
    binding_type = forms.ChoiceField(
        choices=[
            ('perfect', 'Perfect Binding'),
            ('spiral', 'Spiral Binding'),
            ('hardcover', 'Hardcover'),
            ('stapled', 'Stapled')
        ],
        required=False
    )
    has_spine = forms.BooleanField(required=False)
    spine_size_mm = forms.FloatField(required=False)
    paper_type = forms.ChoiceField(
        choices=[("matte", "Matte"), ("glossy", "Glossy"), ('book_paper', 'Book Paper')],
        required=False
    )
    cover_type = forms.ChoiceField(
        choices=[("matte", "Matte"), ("glossy", "Glossy")],
        required=False
    )
    paper_size = forms.CharField(max_length=50, required=False)

    # Apparel fields
    size = forms.CharField(max_length=20, required=False)
    material = forms.CharField(max_length=100, required=False)

    # Plate / banner
    plate_diameter_cm = forms.FloatField(required=False)
    design_file = forms.FileField(required=False)

    def __init__(self, *args, **kwargs):
        products_queryset = kwargs.pop('products_queryset', None)
        super().__init__(*args, **kwargs)
        if products_queryset:
            self.fields['product'].queryset = products_queryset

            # Add data-category attribute to each option
            for product in products_queryset:
                self.fields['product'].widget.choices.queryset = products_queryset
            self.fields['product'].widget.attrs.update({
                "class": "mt-1 block w-full rounded-md border-gray-300 p-2"
            })
class Item(forms.ModelForm):
    """
    creating Item form
    """

    class Meta:
        model = OrderItem
        fields = '__all__'

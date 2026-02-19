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
    """ Form used by client to create an order, styled with Tailwind CSS. """
    name = forms.CharField(max_length=150)
    category_code = forms.CharField(required=True, initial=1)
    quantity = forms.IntegerField(min_value=1, required=True)
    color_mode = forms.CharField(max_length=50, required=False)
    design_type = forms.ChoiceField(choices=DESIGN_CHOICES, required=False)
    description = forms.CharField(widget=forms.Textarea, required=False)
    paper_type = forms.ChoiceField(choices=PAPER_CHOICES, required=False)
    editing_type = forms.ChoiceField(choices=EDIT_CHOICES, required=False)
    paper_size = forms.CharField(max_length=50, required=False)
    number_of_pages = forms.IntegerField(min_value=1, required=True)
    has_spine = forms.BooleanField(initial=False)
    spine_size_mm = forms.FloatField(required=True)
    binding_type = forms.ChoiceField(
        required=True,
        choices=[
            ('perfect', 'Perfect Binding'),
            ('spiral', 'Spiral Binding'),
            ('hardcover', 'Hardcover'),
            ('stapled', 'Stapled'),
        ]
    )
    # Apparel specific
    size = forms.CharField(max_length=20, required=True)
    material = forms.CharField(max_length=100, required=False)
    # Plate specific
    plate_diameter_cm = forms.FloatField(required=False)
    design_file = forms.FileField(required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        input_classes = "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border"
        checkbox_classes = "focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"

        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = checkbox_classes
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs['class'] = "mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-600 hover:file:bg-indigo-100"
            else:
                field.widget.attrs['class'] = input_classes
    
class Item(forms.ModelForm):
    """
    creating Item form
    """

    class Meta:
        model = OrderItem
        fields = '__all__'

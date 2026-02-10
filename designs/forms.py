from django import forms
from .models import Design

class DesignUploadForm(forms.ModelForm):
    """
    Design file upload form
    """
    class Meta:
        model = Design
        fields = ["file"]
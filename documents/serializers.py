from rest_framework import serializers
from .models import LegalDocument

class LegalDocumentSerializer(serializers.ModelSerializer):
    """
    Serializer for legal documents.
    """
    class Meta:
        model = LegalDocument
        fields = "__all__"

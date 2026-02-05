from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from .models import LegalDocument
from .serializers import LegalDocumentSerializer
# Create your views here.
class LegalDocumentViewSet(ModelViewSet):
    """
    Admin generates and views documents.
    """
    queryset = LegalDocument.objects.all()
    serializer_class = LegalDocumentSerializer
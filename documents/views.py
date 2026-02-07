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

def document_list_template(request):
    """
    Admin-only: View all legal documents.
    """
    if not request.user.is_authenticated or request.user.role != "admin":
        return render(request, "forbidden.html", status=403)

    documents = LegalDocument.objects.all()
    return render(request, "document_list.html", {"documents": documents})

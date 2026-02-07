from rest_framework.routers import DefaultRouter
from .views import LegalDocumentViewSet,document_list_template
from django.urls import path
router = DefaultRouter()
router.register("documents", LegalDocumentViewSet)

urlpatterns = router.urls

urlpatterns += [
    path("view/documents/", document_list_template, name="document_list_template"),
]


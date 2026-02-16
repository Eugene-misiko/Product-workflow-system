from rest_framework.routers import DefaultRouter
from .views import DesignViewSet, DesignRequestViewSet, design_list_template, design_request_list_template,mark_design_completed,upload_design
from django.urls import path
router = DefaultRouter()
router.register("designs", DesignViewSet)
router.register("design-requests", DesignRequestViewSet)

urlpatterns = router.urls

urlpatterns += [
    path("view/designs/", design_list_template, name="design_list"),
    path("view/design-requests/", design_request_list_template, name="design_request_list_template"),
    path("view/design/<int:design_id>/complete/", mark_design_completed, name="mark_design_completed"),
    path("upload-design/<int:order_id>/", upload_design, name="upload_design"),
]

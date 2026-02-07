from rest_framework.routers import DefaultRouter
from .views import DesignViewSet, DesignRequestViewSet, design_list_template, design_request_list_template
from django.urls import path
router = DefaultRouter()
router.register("designs", DesignViewSet)
router.register("design-requests", DesignRequestViewSet)

urlpatterns = router.urls

urlpatterns += [
    path("view/designs/", design_list_template, name="design_list_template"),
    path("view/design-requests/", design_request_list_template, name="design_request_list_template"),
]

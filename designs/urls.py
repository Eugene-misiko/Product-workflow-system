from rest_framework.routers import DefaultRouter
from .views import DesignViewSet, DesignRequestViewSet

router = DefaultRouter()
router.register(r"designs", DesignViewSet)
router.register(r"design-requests", DesignRequestViewSet)

urlpatterns = [router.urls]

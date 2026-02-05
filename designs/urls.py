from rest_framework.routers import DefaultRouter
from .views import DesignViewSet, DesignRequestViewSet

router = DefaultRouter()
router.register("designs", DesignViewSet)
router.register("design-requests", DesignRequestViewSet)

urlpatterns = router.urls

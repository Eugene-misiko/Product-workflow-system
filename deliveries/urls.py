from rest_framework.routers import DefaultRouter
from .views import DeliveryViewSet

router = DefaultRouter()
router.register("deliveries", DeliveryViewSet)

urlpatterns = router.urls

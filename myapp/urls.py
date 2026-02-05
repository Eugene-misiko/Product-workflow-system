from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ProductViewSet

router = DefaultRouter()
router.register("categories", CategoryViewSet)
router.register("myapp", ProductViewSet)

urlpatterns = router.urls


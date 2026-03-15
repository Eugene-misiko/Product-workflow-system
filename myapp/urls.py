from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, CategoryViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='products')
urlpatterns = router.urls
urlpatterns += [
    path("categories", CategoryViewSet, name="categories")
]










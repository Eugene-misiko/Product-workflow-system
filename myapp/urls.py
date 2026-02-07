from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ProductViewSet,category_list_template, product_list_template
from django.urls import path

router = DefaultRouter()
router.register("categories", CategoryViewSet)
router.register("myapp", ProductViewSet)

urlpatterns = router.urls

urlpatterns += [
    path("view/categories/", category_list_template, name="category_list_template"),
    path("view/products/", product_list_template, name="product_list_template"),
]


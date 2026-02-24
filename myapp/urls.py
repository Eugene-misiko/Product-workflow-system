from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ProductViewSet,product_detail, product_list
from django.urls import path

router = DefaultRouter()
router.register("categories", CategoryViewSet)
router.register("myapp", ProductViewSet)

urlpatterns = router.urls

urlpatterns += [
    path("view/products/<slug:category_slug>/", product_list, name="product_list_by_category"),
    path('product/<int:id>/<slug>/', product_detail, name="product_detail"),
]


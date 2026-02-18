from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ProductViewSet,product_detail,category_list_template, product_list_template, subscribe
from django.urls import path

router = DefaultRouter()
router.register("categories", CategoryViewSet)
router.register("myapp", ProductViewSet)

urlpatterns = router.urls

urlpatterns += [
    path("view/categories/", category_list_template, name="category_list_template"),
    path("view/products/<slug:category_slug>/", product_list_template, name="product_list_template"),
    path('view/subscribe/', subscribe, name='subscribe'),
    path('<product>/<int:id>/<slug>/', product_detail, name="product_detail")
]


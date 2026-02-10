from rest_framework.routers import DefaultRouter
from .views import OrderViewSet,orders_list, order_detail_template, order_create
from django.urls import path
router = DefaultRouter()
router.register("orders", OrderViewSet)


urlpatterns = router.urls
urlpatterns += [
    path("view/orders/", orders_list, name="orders_list"),
    path("view/orders/<int:order_id>/", order_detail_template, name="order_detail_template"),
    path("view/create", order_create, name="order_create")
]
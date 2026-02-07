from rest_framework.routers import DefaultRouter
from .views import OrderViewSet,order_list_template, order_detail_template
from django.urls import path
router = DefaultRouter()
router.register("orders", OrderViewSet)


urlpatterns = router.urls
urlpatterns += [
    path("view/orders/", order_list_template, name="order_list_template"),
    path("view/orders/<int:order_id>/", order_detail_template, name="order_detail_template"),
]
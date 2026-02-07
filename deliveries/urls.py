from rest_framework.routers import DefaultRouter
from .views import DeliveryViewSet,delivery_list_template
from django.urls import path

router = DefaultRouter()
router.register("deliveries", DeliveryViewSet)

urlpatterns = router.urls
urlpatterns += [
    path("view/deliveries/", delivery_list_template, name="delivery_list_template"),
]
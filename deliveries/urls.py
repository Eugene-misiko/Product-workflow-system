from rest_framework.routers import DefaultRouter
from .views import DeliveryViewSet,delivery_list_template, create_delivery, update_delivery_status, track_delivery, report_delivery_issue
from django.urls import path

router = DefaultRouter()
router.register("deliveries", DeliveryViewSet)

urlpatterns = router.urls
urlpatterns += [
    path("view/deliveries/", delivery_list_template, name="delivery_list_template"),
    path("create/<int:order_id>/", create_delivery, name="create_delivery"),
    path("update/<int:order_id>/", update_delivery_status, name="update_delivery_status"),
    path("track/<int:order_id>/", track_delivery, name="track_delivery"),
    path("report-issue/<int:order_id>/",report_delivery_issue, name="report_delivery_issue"),
]
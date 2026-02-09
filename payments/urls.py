from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, payments_list, payment_create
from django.urls import path
router = DefaultRouter()
router.register("payments", PaymentViewSet)

urlpatterns = router.urls

urlpatterns += [
    path("view/payments/", payments_list, name="payment_list_template"),
    path("view/payments/create/int:order\_id/", payment_create, name="payment_create"),
]
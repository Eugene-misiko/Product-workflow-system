from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, payment_list_template
from django.urls import path
router = DefaultRouter()
router.register("payments", PaymentViewSet)

urlpatterns = router.urls

urlpatterns += [
    path("view/payments/", payment_list_template, name="payment_list_template"),
]
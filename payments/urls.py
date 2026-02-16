from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet,stk_push,mpesa_callback, payments_list, payment_create
from django.urls import path
router = DefaultRouter()
router.register("payments", PaymentViewSet)

urlpatterns = router.urls

urlpatterns += [
    path("view/payments/", payments_list, name="payment_list_template"),
    path("view/payments/create/<int:order_id>/", payment_create, name="payment_create"),
    path("api/stk_push/", stk_push, name="stk_push"),
    path("api/mpesa_callback/", mpesa_callback, name="mpesa_callback"),    
]
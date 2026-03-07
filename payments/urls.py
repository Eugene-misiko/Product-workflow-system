from django.urls import path, re_path
from payments.views import *

urlpatterns = [
    re_path(r'^stk-push/?$', stk_push, name='stk_push'),
    path('pay/', initiate_payment_view, name='payment-ui'),
    path('stk_push/', stk_push, name='stk_push'),
    path('callback/', mpesa_callback, name='mpesa_callback'),
]
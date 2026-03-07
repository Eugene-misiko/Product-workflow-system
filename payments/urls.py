from django.urls import path, re_path
from payments.views import *

urlpatterns = [
    path('stk_push/', stk_push, name='stk_push'),
    path('callback/', mpesa_callback, name='mpesa_callback'),
    path("invoice/<int:order_id>/", download_invoice),
    path("receipt/<int:receipt_id>/", download_receipt),
]
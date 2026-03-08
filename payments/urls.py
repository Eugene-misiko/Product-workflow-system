from django.urls import path
from payments.views import *

urlpatterns = [
    path('stk-push/', stk_push, name='stk_push'),
    path('callback/', mpesa_callback, name='mpesa_callback'),
    path("receipt/<int:receipt_id>/download", download_receipt, name="download_receipt"),
]
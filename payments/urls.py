from rest_framework.routers import DefaultRouter
from .views import  mpesa_callback, payments_list, payment_create
from django.urls import path




urlpatterns= [
    path("view/payments/", payments_list, name="payment_list_template"),
    path("view/payments/create/<int:order_id>/", payment_create, name="payment_create"),
    path("api/mpesa_callback/", mpesa_callback, name="mpesa_callback"),    
]
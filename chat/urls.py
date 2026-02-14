from django.urls import path
from .views import order_chat

urlpatterns = [
    path("view/order/<int:order_id>/chat/", order_chat, name="order_chat"),
]
from django.urls import path
from .views import AdminSummaryView

urlpatterns = [
    path("admin/summary/", AdminSummaryView.as_view()),
]

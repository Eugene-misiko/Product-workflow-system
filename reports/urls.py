from django.urls import path
from .views import AdminSummaryView, admin_summary_template

urlpatterns = [
    path("admin/summary/", AdminSummaryView.as_view()),
    path("view/admin/summary/", admin_summary_template, name="admin_summary_template"),
]

from django.urls import path
from . import views

app_name = 'companies'

urlpatterns = [
    # Company Info
    path('company/', views.CompanyDetailView.as_view(), name='company_detail'),
    path('company/update/', views.CompanyUpdateView.as_view(), name='company_update'),
    # Settings
    path('company/settings/', views.CompanySettingsView.as_view(), name='company_settings'),
    path('company/payment-settings/', views.PaymentSettingsView.as_view(), name='payment_settings'),
    # Dashboard
    path('company/dashboard/', views.CompanyDashboardView.as_view(), name='company_dashboard'),
    # Staff
    path('company/staff/', views.StaffListView.as_view(), name='staff_list'),
    path('company/staff/stats/', views.StaffStatsView.as_view(), name='staff_stats'),
]
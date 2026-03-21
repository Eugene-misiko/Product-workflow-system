from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views
from . import mpesa_views
from django.urls import include
router = DefaultRouter()
router.register(r'invoices', views.InvoiceViewSet, basename='invoice')
router.register(r'payments', views.PaymentViewSet, basename='payment')
router.register(r'receipts', views.ReceiptViewSet, basename='receipt')

app_name = 'payments'

urlpatterns = [
    path('', include(router.urls)),
    # Invoice actions
    path('invoices/<int:pk>/download/', views.download_invoice, name='download_invoice'),
    path('invoices/<int:pk>/send/', views.send_invoice, name='send_invoice'),
    path('invoices/pending-deposit/', views.PendingDepositInvoicesView.as_view(), name='pending_deposit'),
    path('invoices/pending-balance/', views.PendingBalanceInvoicesView.as_view(), name='pending_balance'),
    # Receipt actions
    path('receipts/<int:pk>/download/', views.download_receipt, name='download_receipt'),
    # M-Pesa
    path('mpesa/stk-push/', mpesa_views.stk_push, name='mpesa_stk_push'),
    path('mpesa/callback/', mpesa_views.mpesa_callback, name='mpesa_callback'),
    # Manual payment
    path('record-payment/', views.RecordPaymentView.as_view(), name='record_payment'),
    # Stats
    path('payment-stats/', views.PaymentStatsView.as_view(), name='payment_stats'),
]


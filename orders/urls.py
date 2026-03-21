from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'print-jobs', views.PrintJobViewSet, basename='print-job')
router.register(r'transportation', views.TransportationViewSet, basename='transportation')

app_name = 'orders'

urlpatterns = [
    path('', include(router.urls)),
    
    # Order workflow
    path('orders/<int:pk>/assign-designer/', views.AssignDesignerView.as_view(), name='assign_designer'),
    path('orders/<int:pk>/assign-printer/', views.AssignPrinterView.as_view(), name='assign_printer'),
    path('orders/<int:pk>/start-design/', views.StartDesignView.as_view(), name='start_design'),
    path('orders/<int:pk>/submit-design/', views.SubmitDesignView.as_view(), name='submit_design'),
    path('orders/<int:pk>/approve-design/', views.ApproveDesignView.as_view(), name='approve_design'),
    path('orders/<int:pk>/cancel/', views.CancelOrderView.as_view(), name='cancel_order'),
    
    # Print job actions
    path('print-jobs/<int:pk>/start/', views.StartPrintJobView.as_view(), name='start_print_job'),
    path('print-jobs/<int:pk>/polishing/', views.MoveToPolishingView.as_view(), name='move_to_polishing'),
    path('print-jobs/<int:pk>/complete/', views.CompletePrintJobView.as_view(), name='complete_print_job'),
    
    # Dashboard
    path('my-orders/', views.ClientOrderListView.as_view(), name='my_orders'),
    path('my-assignments/', views.DesignerAssignmentListView.as_view(), name='my_assignments'),
    path('my-print-jobs/', views.PrinterJobListView.as_view(), name='my_print_jobs'),
    path('unassigned/', views.UnassignedOrdersView.as_view(), name='unassigned_orders'),
]


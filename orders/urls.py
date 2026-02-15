from rest_framework.routers import DefaultRouter
from .views import OrderViewSet,orders_list, order_detail_template, order_create,order_approve,order_reject,move_to_delivery,move_to_design,move_to_printing,confirm_delivery,delete_order ,choose_delivery_mode,confirm_arrival,report_delivery_issue
from django.urls import path
router = DefaultRouter()
router.register("orders", OrderViewSet)


urlpatterns = router.urls
urlpatterns += [
    path("view/orders/", orders_list, name="orders_list"),
    path("view/orders/<int:order_id>/", order_detail_template, name="order_detail"),
    path("view/create", order_create, name="order_create"),
    path('view/<int:order_id>/reject/', order_reject, name='order_reject'),
    path('view/<int:order_id>/approve/', order_approve, name='order_approve'),
    path('view/<int:order_id>/design/', move_to_design, name='move_to_design'),
    path('view/<int:order_id>/printing/', move_to_printing, name='move_to_printing'),
    path('view/<int:order_id>/delivery/', move_to_delivery, name='move_to_delivery'),
    path('view/<int:order_id>/confirm/', confirm_delivery, name='confirm_delivery'),
    path('view/<int:order_id>/delivery-mode/', choose_delivery_mode, name='choose_delivery_mode'),
    path('view/<int:order_id>/confirm-arrival/', confirm_arrival, name='confirm_arrival'),
    path('view/<int:order_id>/report-issue/', report_delivery_issue, name='report_delivery_issue'),
    path("view/order/<int:order_id>/delete/", delete_order, name="delete_order"),
    path('products-by-category/<int:category_id>/', products_by_category, name='products_by_category'),


]
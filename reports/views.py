from rest_framework.views import APIView
from rest_framework.response import Response
from orders.models import Order
from payments.models import Payment
from django.shortcuts import render
# Create your views here.


class AdminSummaryView(APIView):
    """
    Admin dashboard summary.
    """
    def get(self, request):
        if request.user.role != "admin":
            return Response({"error": "Forbidden"}, status=403)

        return Response({
            "orders": Order.objects.count(),
            "payments": Payment.objects.count(),
        })
    
def admin_summary_template(request):
    """
    Admin-only dashboard summary.
    """
    if not request.user.is_authenticated or request.user.role != "admin":
        return render(request, "forbidden.html", status=403)

    context = {
        "orders_count": Order.objects.count(),
        "payments_count": Payment.objects.count(),
    }
    return render(request, "admin_summary.html", context)    

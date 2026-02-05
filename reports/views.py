from rest_framework.views import APIView
from rest_framework.response import Response
from orders.models import Order
from payments.models import Payment
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

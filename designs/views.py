from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Design, DesignRequest
from .serializers import DesignSerializer,DesignRequestSerializer

# Create your views here.
 

class DesignViewSet(ModelViewSet):
    """
    Client uploads designs, designer updates status.
    """
    queryset = Design.objects.all()
    serializer_class = DesignSerializer

    def get_queryset(self):
        """
        Designer sees only assigned designs.
        Admin sees all designs.
        """        
        user = self.request.user
        if user.role == "designer":
            return Design.objects.filter(order__designrequest__designer=user)
        return Design.objects.all()

    @action(detail=True, methods=["put"])
    def status(self, request, pk=None):
        design = self.get_object()
        design.status = request.data.get("status")
        design.save()
        return Response({"message": "Design status updated"})


class DesignRequestViewSet(ModelViewSet):
    """
    Admin assigns designers.
    """
    queryset = DesignRequest.objects.all()
    serializer_class = DesignRequestSerializer

def design_list_template(request):
    """
    Display designs in HTML.
    Designer sees only assigned designs.
    Admin sees all designs.
    """
    if not request.user.is_authenticated:
        return render(request, "forbidden.html", status=403)

    user = request.user
    if user.role == "designer":
        designs = Design.objects.filter(order__designrequest__designer=user)
    elif user.role == "admin":
        designs = Design.objects.all()
    else:
        designs = Design.objects.none()

    return render(request, "design_list.html", {"designs": designs})


def design_request_list_template(request):
    """
    Admin-only: View all design requests.
    """
    if not request.user.is_authenticated or request.user.role != "admin":
        return render(request, "forbidden.html", status=403)

    requests = DesignRequest.objects.all()
    return render(request, "design_request_list.html", {"requests": requests})    

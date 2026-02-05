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

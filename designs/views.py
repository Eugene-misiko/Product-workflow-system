from django.shortcuts import render, redirect,get_object_or_404
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from django.contrib.auth.decorators import login_required
from rest_framework.response import Response
from .models import Design, DesignRequest
from .serializers import DesignSerializer,DesignRequestSerializer
from .forms import DesignUploadForm
from notifications.utils import notify
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


@login_required
def upload_design(request, order_id):
    """
    Client uploads a design file.
    """
    # Only clients can upload designs
    if request.user.role != "client":
        return render(request, "forbidden.html", status=403)

    if request.method == "POST":
        form = DesignUploadForm(request.POST, request.FILES)
        if form.is_valid():
            design = form.save(commit=False)
            design.order_id = order_id  
            design.save()
            return redirect("designs_list")
    else:
        form = DesignUploadForm()

    return render(request, "design_upload.html", {"form": form}) 
@login_required
def mark_design_completed(request, design_id):
    """
    Designer marks a design as completed.
    Order automatically moves to printing stage.
    """

    if request.user.role != "designer":
        return render(request, "forbidden.html", status=403)

    design = get_object_or_404(Design, id=design_id)

    # Ensure designer owns this task##
    if design.order.designrequest.designer != request.user:
        return render(request, "forbidden.html", status=403)

    # Update design status
    design.status = "completed"
    design.save()

    # Update order status to printing
    order = design.order
    if order.status == "in_design":
        order.status = "on_printing"
        order.save()

    notify(order.client, f"Your order #{order.id} design is completed and is now being printed.")

    return redirect("design_list_template")



@login_required
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

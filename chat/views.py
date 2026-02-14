from django.shortcuts import render,get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Message
from orders.models import Order
# Create your views here.

@login_required
def order_chat(request, order_id):
    """
    Chat page for a specific order.

    - Client can chat with admin
    - Admin can chat with client and designer
    - Designer can chat with admin
    """

    order = get_object_or_404(Order, id=order_id)

    # Access control
    if request.user.role == "client" and order.client != request.user:
        return render(request, "forbidden.html", status=403)

    messages = order.messages.all().order_by("timestamp")

    if request.method == "POST":
        content = request.POST.get("content")

        if content:
            Message.objects.create(
                order=order,
                sender=request.user,
                content=content
            )

        return redirect("order_chat", order_id=order.id)

    return render(request, "chat.html", {
        "order": order,
        "messages": messages
    })

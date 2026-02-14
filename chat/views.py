from django.shortcuts import render,get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Message
from orders.models import Order
from notifications.utils import notify
from accounts.models import User
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

            sender = request.user

            if sender.role == "client":
                admins = User.objects.filter(role="admin")
                for admin in admins:
                    notify(admin, f"New message from client on Order #{order.id}")

            elif sender.role == "designer":
                admins = User.objects.filter(role="admin")
                for admin in admins:
                    notify(admin, f"New message from designer on Order #{order.id}")

            elif sender.role == "admin":
                notify(order.client, f"Admin replied on Order #{order.id}")

                if hasattr(order, "designrequest") and order.designrequest.designer:
                    notify(
                        order.designrequest.designer,
                        f"Admin replied on Order #{order.id}"
                    )

        return redirect("order_chat", order_id=order.id)

    return render(request, "chat.html", {
        "order": order,
        "messages": messages
    })

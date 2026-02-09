from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def profile_page(request):
    """
    HTML profile page for logged-in users.
    """
    return render(request, "profile.html", {
        "user_obj": request.user
    })
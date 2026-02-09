from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import render, redirect  
from .models import User
from .serializers import RegisterSerializer, UserProfileSerializer
from .permissions import IsAdmin
from django.contrib.auth import logout as django_logout
from django.contrib.auth.decorators import login_required
#create your views here

class RegisterView(generics.CreateAPIView):
    """
    Client registration endpoint for creating new users.
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

class LogoutView(APIView):
    """
    Logout user by blacklisting the refresh token (for JWT).
    """
    def post(self, request):
        refresh_token = request.data.get("refresh")
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Logged out successfully"})

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    View or update authenticated user's profile.
    """
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user

class UserListView(generics.ListAPIView):
    """
    Admin-only endpoint to list all users.
    """
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAdmin]

class AssignRoleView(APIView):
    """
    Admin-only endpoint to assign a role to a user.
    """
    permission_classes = [IsAdmin]

    def put(self, request, user_id):
        role = request.data.get("role")
        if role not in ["client", "admin", "designer"]:
            return Response({"error": "Invalid role"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.get(id=user_id)
        user.role = role
        user.save()

        return Response({"message": "Role updated successfully"})

@login_required
def user_profile_template(request):
    """
    Render the logged-in user's profile.
    """
    return render(request, "user_profile.html", {"user": request.user})


@login_required
def post_login_redirect(request):
    """
    Redirect users after login based on role.
    """
    user = request.user

    if user.role == "admin":
        return redirect("/api/view/admin/summary/")
    elif user.role == "designer":
        return redirect("/api/view/designs/")
    elif user.role == "client":
        return redirect("/api/view/orders/")
    else:
        return redirect("logout")


def logout(request):
    """
    Log the user out and redirect to login page.
    """
    django_logout(request)
    return redirect("/auth/login/")





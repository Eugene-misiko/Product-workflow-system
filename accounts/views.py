from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import render  
from .models import User
from .serializers import RegisterSerializer, UserProfileSerializer
from .permissions import IsAdmin

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

def user_list_template(request):
    """
    Admin-only: Render all users in an HTML table.
    """
    if not request.user.is_authenticated or request.user.role != "admin":
        return render(request, "forbidden.html", status=403)

    users = User.objects.all()
    return render(request, "user_list.html", {"users": users})

def user_profile_template(request):
    """
    Render the logged-in user's profile.
    """
    if not request.user.is_authenticated:
        return render(request, "forbidden.html", status=403)

    return render(request, "user_profile.html", {"user": request.user})




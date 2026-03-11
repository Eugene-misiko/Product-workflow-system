from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from .serializers import RegisterSerializer, UserProfileSerializer
from .permissions import IsAdmin
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404

# create your views here
class RegisterView(generics.CreateAPIView):
    """
    Public registration endpoint.
    All new users are automatically assigned the CLIENT role.
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class LoginView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        first_name = request.data.get("first_name")
        password = request.data.get("password")

        user = authenticate(first_name=first_name, password=password)

        if user is not None:

            refresh = RefreshToken.for_user(user)

            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "id": user.id,
                    "first_name": user.first_name,
                    "role": user.role,
                }
            })

        return Response(
            {"error": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED
        )


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
    permission_classes = [IsAdmin]
    def put(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        role = request.data.get("role")

        if role not in ["client", "admin", "designer", "printer"]:
            return Response(
                {"error": "Invalid role"},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.role = role
        user.save()
        return Response({"message": "Role updated successfully"})
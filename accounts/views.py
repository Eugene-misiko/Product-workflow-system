from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from .serializers import RegisterSerializer, UserProfileSerializer
from .permissions import IsAdmin


class RegisterView(generics.CreateAPIView):
    """
    Client registration endpoint.
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class LogoutView(APIView):
    """
    Logout user by blacklisting refresh token.
    """
    def post(self, request):
        refresh_token = request.data.get("refresh")
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Logged out successfully"})


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    View or update the authenticated user's profile.
    """
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user


class UserListView(generics.ListAPIView):
    """
    Admin-only: list all users.
    """
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAdmin]


class AssignRoleView(APIView):
    """
    Admin-only: assign role to a user.
    """
    permission_classes = [IsAdmin]

    def put(self, request, user_id):
        role = request.data.get("role")

        if role not in ["client", "admin", "designer"]:
            return Response(
                {"error": "Invalid role"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.get(id=user_id)
        user.role = role
        user.save()

        return Response({"message": "Role updated successfully"})


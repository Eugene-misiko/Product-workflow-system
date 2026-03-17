from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from .serializers import RegisterSerializer, UserProfileSerializer,LoginSerializer
from .permissions import IsAdmin
from django.contrib.auth import authenticate, get_user_model
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated

# create your views here
User = get_user_model()
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

        try:
            # Find the user by first_name
            user = User.objects.get(first_name=first_name)
        except User.DoesNotExist:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        # Check password manually
        if not user.check_password(password):
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        # Generate JWT tokens
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


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response({"message": "Logged out successfully"})

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    View or update authenticated user's profile.
    Supports avatar upload via multipart/form-data.
    """
    serializer_class = UserProfileSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

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
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_bytes
from django.conf import settings  
from .models import User
from .serializers import (
    RegisterSerializer, 
    UserProfileSerializer, 
    LoginSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)
from .permissions import IsAdmin
#create your views here

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        user = authenticate(request, username=email, password=password)

        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "id": user.id,
                    "first_name": user.first_name,
                    "email": user.email,
                    "role": user.role,
                }
            })
        else:
            return Response(
                {"error": "Invalid email or password"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            
            token = default_token_generator.make_token(user)
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            
            relative_link = f"/reset-password?uidb64={uidb64}&token={token}"
            absolute_link = f"{settings.FRONTEND_URL}{relative_link}"

            subject = "Reset Your Password"
            
            plain_message = f"""
                    Hi {user.first_name},

                    Click the link below to reset your password:
                    <{absolute_link}>

                    If you didn't request this, ignore this email.
                    """
            # 2. Send HTML email for real email clients
            html_message = f"""
                <p>Hi {user.first_name},</p>
                <p><a href="{absolute_link}">Reset Password</a></p>
                """
            
            send_mail(
                subject, 
                plain_message, 
                settings.EMAIL_HOST_USER, 
                [email], 
                html_message=html_message
            )
            
            return Response({"message": "Password reset link sent."}, status=200)
            
        except User.DoesNotExist:
            return Response({"message": "If user exists, link sent."}, status=200)

class PasswordResetConfirmView(generics.GenericAPIView):
    """
    Confirm the password reset.
    """
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Password has been reset successfully."}, 
            status=status.HTTP_200_OK
        )

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class UserListView(generics.ListAPIView):
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
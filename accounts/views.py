"""
Account Views - Authentication, User Management, Invitations
"""
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from .models import Invitation, PasswordResetToken, UserProfile
from .serializers import (
    UserSerializer, UserDetailSerializer, UserUpdateSerializer,
    RegisterSerializer, LoginSerializer, ChangePasswordSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    InvitationSerializer, CreateInvitationSerializer,
)


User = get_user_model()

class RegisterView(generics.CreateAPIView):
    """
    Register a new user via invitation
    """
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'Registration successful!'
        }, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    """
    Login view - returns JWT tokens
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        user = authenticate(email=email, password=password)
        
        if user is None:
            return Response({
                'error': 'Invalid email or password.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_active:
            return Response({
                'error': 'This account has been deactivated.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })

class LogoutView(APIView):
    """
    Logout view - blacklists the refresh token
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': 'Successfully logged out.'})
        except Exception:
            return Response({'message': 'Successfully logged out.'})  

class ProfileView(generics.RetrieveUpdateAPIView):
    """
    Get or update current user profile
    """
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserDetailSerializer
        return UserUpdateSerializer

class ChangePasswordView(APIView):
    """
    Change password for authenticated user
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Password changed successfully.'})

class PasswordResetRequestView(APIView):
    """
    Request password reset email
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['email']
        
        # Create reset token
        reset_token = PasswordResetToken.objects.create(user=user)
        
        # Send email
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{reset_token.token}"
        send_mail(
            subject='Password Reset - PrintFlow',
            message=f'Click the following link to reset your password: {reset_url}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
        
        return Response({
            'message': 'Password reset email sent. Please check your inbox.'
        })

class PasswordResetConfirmView(APIView):
    """
    Confirm password reset with token
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Password reset successful. You can now login.'})

# Invitation Views
class InvitationListView(generics.ListCreateAPIView):
    """
    List and create invitations (Admin only)
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Invitation.objects.filter(company=self.request.user.company)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateInvitationSerializer
        return InvitationSerializer
    
    def perform_create(self, serializer):
        invitation = serializer.save()
        
        # Send invitation email
        invite_url = f"{settings.FRONTEND_URL}/register/{invitation.token}"
        send_mail(
            subject=f'Invitation to join {invitation.company.name}',
            message=f'''
            You have been invited to join {invitation.company.name} as a {invitation.get_role_display()}.
            
            {invitation.message}
            
            Click the following link to register: {invite_url}
            
            This invitation expires on {invitation.expires_at.strftime("%Y-%m-%d %H:%M")}.
            ''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invitation.email],
            fail_silently=True,
        )
class InvitationDetailView(generics.RetrieveAPIView):
    """
    Get invitation details (for registration page)
    """
    permission_classes = [AllowAny]
    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer
    lookup_field = 'token'    
class CancelInvitationView(APIView):
    """
    Cancel a pending invitation
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        invitation = get_object_or_404(
            Invitation,
            pk=pk,
            company=request.user.company
        )
        
        if invitation.status != Invitation.STATUS_PENDING:
            return Response({
                'error': 'Can only cancel pending invitations.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        invitation.cancel()
        return Response({'message': 'Invitation cancelled.'})

# User Management Views (Admin only)
class UserListView(generics.ListAPIView):
    """
    List all users in the company (Admin only)
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_queryset(self):
        return User.objects.filter(company=self.request.user.company)

class UserDetailView(generics.RetrieveUpdateAPIView):
    """
    Get or update a user (Admin only)
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_queryset(self):
        return User.objects.filter(company=self.request.user.company)
    
    def update(self, request, *args, **kwargs):
        user = self.get_object()
        
        # Only admin can change roles
        if 'role' in request.data and request.user.role != User.ADMIN:
            return Response({
                'error': 'Only admin can change user roles.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Cannot change admin role
        if user.role == User.ADMIN and 'role' in request.data:
            return Response({
                'error': 'Cannot change admin role.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return super().update(request, *args, **kwargs)    
class DeactivateUserView(APIView):
    """
    Deactivate a user account (Admin only)
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        user = get_object_or_404(
            User,
            pk=pk,
            company=request.user.company
        )
        
        if user.role == User.ADMIN:
            return Response({
                'error': 'Cannot deactivate admin account.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        user.is_active = False
        user.save()
        
        return Response({'message': f'User {user.email} has been deactivated.'})        


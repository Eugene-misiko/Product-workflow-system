"""
Account Views - Authentication and User Management.

This module provides:
1. Authentication (login, logout, token refresh)
2. User registration (via invitation)
3. Company registration (creates admin automatically)
4. User management (admin manages company users)
5. Invitation management

"""
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404

from .models import Invitation, PasswordResetToken, UserProfile, User
from .serializers import (
    UserSerializer, UserDetailSerializer, UserUpdateSerializer,
    RegisterSerializer, LoginSerializer, ChangePasswordSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    InvitationSerializer, CreateInvitationSerializer,
    CompanyRegistrationSerializer, CompanyInvitationSerializer,
)
from companies.models import Company, CompanySettings, CompanyInvitation

User = get_user_model()

# AUTHENTICATION VIEWS

class LoginView(APIView):
    """
    User Login View.
    
    Authenticate user and return JWT tokens.
    
    Request Body:
        email: User email
        password: User password
    
    Returns:
        user: User data
        tokens: JWT tokens (access and refresh)
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
    User Logout View.
    
    Blacklists the refresh token to prevent further use.
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
    User Profile View.
    
    Get or update current user's profile.
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
    Change Password View.
    
    Change password for authenticated user.
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
    Request Password Reset View.
    
    Send password reset email to user.
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
            subject=f'Password Reset - {user.company.name if user.company else "PrintFlow"}',
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
    Confirm Password Reset View.
    
    Reset password using token from email.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Password reset successful. You can now login.'})


# =====================
# REGISTRATION VIEWS
# =====================

class RegisterView(generics.CreateAPIView):
    """
    User Registration View (via Invitation).
    
    Register a new user using an invitation token.
    The user is automatically assigned to the company
    and given the role specified in the invitation.
    
    Request Body:
        invitation_token: Token from invitation email
        email: User email (must match invitation)
        password: User password
        first_name: First name
        last_name: Last name
        phone: Phone number (optional)
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


class CompanyRegistrationView(generics.CreateAPIView):
    """
    Company Registration View.
    
    Register a new company. The registering user becomes
    the company admin automatically.
    This is how new companies join the platform:
    1. User fills out company regstration form
    2. System creates company
    3. System creates user as company admin
    4. User can immediately start managing their company
    
    Request Body:
        company_name: Name of the company
        company_slug: URL-friendly identifier
        company_email: Company email
        company_phone: Company phone
        company_address: Company address
        admin_first_name: Admin's first name
        admin_last_name: Admin's last name
        admin_email: Admin's email
        admin_password: Admin's password
        admin_phone: Admin's phone (optional)
    """
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = CompanyRegistrationSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create company
        company = Company.objects.create(
            name=serializer.validated_data['company_name'],
            slug=serializer.validated_data['company_slug'],
            email=serializer.validated_data['company_email'],
            phone=serializer.validated_data['company_phone'],
            address=serializer.validated_data['company_address'],
            city=serializer.validated_data.get('company_city', ''),
            country=serializer.validated_data.get('company_country', 'Kenya'),
        )
        
        # Create company settings
        CompanySettings.objects.create(company=company)
        
        # Create admin user
        admin = User.objects.create_user(
            email=serializer.validated_data['admin_email'],
            password=serializer.validated_data['admin_password'],
            first_name=serializer.validated_data['admin_first_name'],
            last_name=serializer.validated_data['admin_last_name'],
            phone=serializer.validated_data.get('admin_phone', ''),
            role=User.ADMIN,
            company=company,
            email_verified=True,
            email_verified_at=timezone.now(),
        )
        
        # Set company admin
        company.admin = admin
        company.save()
        
        # Create user profile
        UserProfile.objects.get_or_create(user=admin)
        
        # Generate tokens
        refresh = RefreshToken.for_user(admin)
        
        return Response({
            'user': UserSerializer(admin).data,
            'company': {
                'id': company.id,
                'name': company.name,
                'slug': company.slug,
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': f'Company "{company.name}" registered successfully! You are now the admin.'
        }, status=status.HTTP_201_CREATED)


# USER MANAGEMENT VIEWS


class UserListView(generics.ListAPIView):
    """
    List Users View.
    
    List all users in the company.
    Company admin can see all users.
    Designers/Printers can see staff.
    Clients can only see themselves.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Platform admin sees all
        if user.is_platform_admin:
            return User.objects.all()
        
        # Company users see their company's users
        if user.company:
            queryset = User.objects.filter(company=user.company)
            
            # Filter by role
            role = self.request.query_params.get('role')
            if role:
                queryset = queryset.filter(role=role)
            
            return queryset
        
        return User.objects.none()


class UserDetailView(generics.RetrieveUpdateAPIView):
    """
    User Detail View.
    
    Get or update a user's details.
    Only admin can update other users.
    Users can update their own profile.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_platform_admin:
            return User.objects.all()
        if user.company:
            return User.objects.filter(company=user.company)
        return User.objects.none()
    
    def update(self, request, *args, **kwargs):
        user = self.get_object()
        
        # Only admin can change roles
        if 'role' in request.data and not request.user.is_company_admin:
            return Response({
                'error': 'Only company admin can change user roles.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Cannot change admin role
        if user.is_company_admin and 'role' in request.data:
            return Response({
                'error': 'Cannot change admin role.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return super().update(request, *args, **kwargs)


class DeactivateUserView(APIView):
    """
    Deactivate User View.
    Deactivate a user account (admin only).
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        if not request.user.is_company_admin:
            return Response({
                'error': 'Only company admin can deactivate users.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        user = get_object_or_404(
            User,
            pk=pk,
            company=request.user.company
        )
        
        if user.is_company_admin:
            return Response({
                'error': 'Cannot deactivate admin account.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        user.is_active = False
        user.save()
        
        return Response({'message': f'User {user.email} has been deactivated.'})

class ChangeUserRoleView(APIView):
    """
    Change User Role View.
    Change a user's role (admin only).
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        if not request.user.is_company_admin:
            return Response({
                'error': 'Only company admin can change user roles.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        user = get_object_or_404(
            User,
            pk=pk,
            company=request.user.company
        )
        
        new_role = request.data.get('role')
        
        if new_role not in [User.DESIGNER, User.PRINTER, User.CLIENT]:
            return Response({
                'error': 'Invalid role. Choose designer, printer, or client.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if user.is_company_admin:
            return Response({
                'error': 'Cannot change admin role.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        user.role = new_role
        user.save()
        
        return Response({
            'message': f'User role changed to {user.get_role_display()}',
            'user': UserSerializer(user).data
        })        

# =====================
# INVITATION VIEWS
# =====================

class InvitationListView(generics.ListCreateAPIView):
    """
    List and Create Invitations View.
    
    Company admin can:
    - List all invitations for their company
    - Create new invitations for designers, printers, clients
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Invitation.objects.filter(
            company=self.request.user.company
        ).order_by('-created_at')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateInvitationSerializer
        return InvitationSerializer
    
    def perform_create(self, serializer):
        if not self.request.user.is_company_admin:
            return Response({
                'error': 'Only company admin can send invitations.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        invitation = serializer.save(
            invited_by=self.request.user,
            company=self.request.user.company
        )
        
        # Send invitation email
        invite_url = f"{settings.FRONTEND_URL}/register/{invitation.token}"
        send_mail(
            subject=f'Invitation to join {invitation.company.name}',
            message=f'''
            You have been invited to join {invitation.company.name} as a {invitation.get_role_display()}. {invitation.message}
            Click the following link to register: {invite_url}
            This invitation expires on {invitation.expires_at.strftime("%Y-%m-%d %H:%M")}.
            ''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invitation.email],
            fail_silently=True,
        )        

class InvitationDetailView(generics.RetrieveAPIView):
    """
    Get Invitation Details View.
    
    Get invitation details using token (for registration page).
    No authentication required.
    """
    permission_classes = [AllowAny]
    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer
    lookup_field = 'token'


class CancelInvitationView(APIView):
    """
    Cancel Invitation View.
    
    Cancel a pending invitation.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        invitation = get_object_or_404(
            Invitation,
            pk=pk,
            company=request.user.company
        )
        
        if not request.user.is_company_admin:
            return Response({
                'error': 'Only company admin can cancel invitations.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if invitation.status != Invitation.STATUS_PENDING:
            return Response({
                'error': 'Can only cancel pending invitations.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        invitation.cancel()
        return Response({'message': 'Invitation cancelled.'})

class ResendInvitationView(APIView):
    """
    Resend Invitation View.
    
    Resend an expired or pending invitation.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        invitation = get_object_or_404(
            Invitation,
            pk=pk,
            company=request.user.company
        )
        
        if not request.user.is_company_admin:
            return Response({
                'error': 'Only company admin can resend invitations.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Reset expiration
        invitation.expires_at = timezone.now() + timezone.timedelta(days=7)
        invitation.status = Invitation.STATUS_PENDING
        invitation.save()
        
        # Send email again
        invite_url = f"{settings.FRONTEND_URL}/register/{invitation.token}"
        send_mail(
            subject=f'Invitation to join {invitation.company.name}',
            message=f'Click the following link to register: {invite_url}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invitation.email],
            fail_silently=True,
        )
        
        return Response({'message': 'Invitation resent successfully'})
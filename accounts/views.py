"""
Accounts App - Views

All views for:
- Authentication (login, logout, token refresh)
- User registration (company registration, invitation acceptance)
- User management (profile, password change)
- Invitation management (create, list, cancel)

NO MANAGEMENT COMMANDS!
- Platform Admin: python manage.py createsuperuser
- Company Admin: POST /api/auth/register-company/
"""
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from .models import User, Invitation, PasswordResetToken, UserProfile
from .serializers import (
    UserSerializer, UserDetailSerializer, UserUpdateSerializer,
    LoginSerializer, ChangePasswordSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    RegisterSerializer, CompanyRegistrationSerializer,
    InvitationSerializer, CreateInvitationSerializer,InvitationDetailSerializer,
    RegisterUserSerializer
)


# =====================
# AUTHENTICATION VIEWS
# =====================

class LoginView(APIView):
    """
    User login - returns JWT tokens.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']

        refresh = RefreshToken.for_user(user)

        return Response({
            'user': {
                **UserSerializer(user).data,
                'company_id': user.company.id if user.company else None,
                'company_name': user.company.name if user.company else None,
                'is_platform_admin': user.is_platform_admin,
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    User logout - blacklists refresh token.
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
    Get or update current user profile.
    
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
    Request password reset email.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        
        # Create reset token
        reset_token = PasswordResetToken.objects.create(user=user)
        
        # Send email
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{reset_token.token}"
        company_name = user.company.name if user.company else "PrintFlow"
        
        send_mail(
            subject=f'Password Reset - {company_name}',
            message=f'''
            Hello {user.get_full_name()},
            You requested to reset your password.
            Click the following link to reset your password:
           {reset_url}
           This link will expire in 24 hours.
           If you did not request this, please ignore this email.
            Best regards,
            {company_name}
            ''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
        
        return Response({
            'message': 'Password reset email sent. Please check your inbox.'
        })


class PasswordResetConfirmView(APIView):
    """
    Confirm password reset with token.
    

    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Password reset successful. You can now login.'})


# =================
# REGISTRATION VIEWS
# ==================


#User registration views
class RegisterUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        refresh = RefreshToken.for_user(user)

        return Response({
            "user": {
                **UserSerializer(user).data,
                "company_id": user.company.id if user.company else None,
                "company_name": user.company.name if user.company else None,
                "is_platform_admin": user.is_platform_admin,
            },
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        }, status=status.HTTP_201_CREATED)
        
class RegisterView(generics.CreateAPIView):
    """
    User registration via invitation.
    This is used when a user accepts an invitation to join
    a company as designer, printer, or client.
    
    """
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': f'Welcome! You have joined {user.company.name}.'
        }, status=status.HTTP_201_CREATED)


class CompanyRegistrationView(generics.CreateAPIView):
    """
    Company registration - creates company and admin user.
    1. User fills out company registration form
    2. System creates company
    3. System creates user as company admin
    4. User can immediately start managing their company

    """
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = CompanyRegistrationSerializer

    def create(self, request, *args, **kwargs):
        from companies.models import Company, CompanySettings

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if User.objects.filter(role=User.ADMIN, company__slug=data['company_slug']).exists():
                return Response({'error': 'This company already has an admin.'}, status=status.HTTP_400_BAD_REQUEST)        
        # Create company
        company = Company.objects.create(
            name=data['company_name'],
            slug=data['company_slug'],
            email=data['company_email'],
            phone=data['company_phone'],
            address=data['company_address'],
            city=data.get('company_city', ''),
            country=data.get('company_country', 'Kenya'),
        )
        
        # Create company settings
        CompanySettings.objects.create(company=company)
        
        # Create admin user
        admin = User.objects.create_user(
            email=data['admin_email'],
            password=data['admin_password'],
            first_name=data['admin_first_name'],
            last_name=data['admin_last_name'],
            phone=data.get('admin_phone', ''),
            role=User.ADMIN,
            company=company,
            email_verified=True,
        )
        
        # Set company admin
        company.admin = admin
        company.save()
        
        # Create profile
        UserProfile.objects.get_or_create(user=admin)
        #acces token
        token = request.data.get("token")

        invitation = get_object_or_404(
            CompanyInvitation,
            token=token,
            status=CompanyInvitation.STATUS_PENDING
        )

        if invitation.expires_at < timezone.now():
            return Response({'error': 'Invitation expired'}, status=400)        
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
        invitation.status = CompanyInvitation.STATUS_ACCEPTED
        invitation.accepted_at = timezone.now()
        invitation.company = company
        invitation.save()        



# =====================
# USER MANAGEMENT VIEWS
# =====================

class UserListView(generics.ListAPIView):
    """
    List users in the company.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_queryset(self):
        user = self.request.user

        # PLATFORM ADMIN 
        if user.is_platform_admin:
            queryset = User.objects.all()

        #  COMPANY ADMIN OR COMPANY USER
        elif user.company:
            queryset = User.objects.filter(company=user.company)

        else:
            return User.objects.none()

        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)

        return queryset


class UserDetailView(generics.RetrieveUpdateAPIView):
    """
    Get or update a user.
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

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer        


class DeactivateUserView(APIView):
    """
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
        if user == request.user:
            return Response({
                'error': 'You cannot deactivate your own account.'
            }, status=status.HTTP_400_BAD_REQUEST)

        if user.is_company_admin:
            return Response({
                'error': 'Cannot deactivate admin account.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        user.is_active = False
        user.save()
        
        return Response({'message': f'User {user.email} has been deactivated.'})


class ChangeUserRoleView(APIView):
    """
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
    List and create invitations (admin only).
    
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user

        # PLATFORM ADMIN- see ALL invitations
        if user.role == "platform_admin":
            return Invitation.objects.all().order_by('-created_at')

        # COMPANY ADMIN- only their company
        if user.company:
            return Invitation.objects.filter(company=user.company).order_by('-created_at')

        return Invitation.objects.none()
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateInvitationSerializer
        return InvitationSerializer
    
    def perform_create(self, serializer):
        user = self.request.user
        role = serializer.validated_data.get("role")
        # PLATFORM ADMIN 
        if user.role == "platform_admin":
            if role != User.ADMIN:
                raise PermissionDenied("Platform admin can only invite company admins.")
            company = serializer.validated_data.get("company")
            if not company:
                raise PermissionDenied("Company is required for admin invitation.")
        # COMPANY ADMIN 
        elif user.role == "admin":
            if role == User.ADMIN:
                raise PermissionDenied("Company admin cannot invite another admin.")
            company = user.company
        else:
            raise PermissionDenied("Not allowed to send invitations.")

        invitation = serializer.save(
            invited_by=user,
            company=company
        )
        # Send invitation email
        if invitation.role == User.ADMIN:
            invite_url = f"{settings.FRONTEND_URL}/register-company?token={invitation.token}"
        else:
            invite_url = f"{settings.FRONTEND_URL}/register?token={invitation.token}"
        
        send_mail(
            subject=f'Invitation to join {invitation.company.name}',
            message=f'''
        Hello, You have been invited to join {invitation.company.name} as a {invitation.get_role_display()}.
       {invitation.message}
       Click the following link to register:
       {invite_url} This invitation expires on {invitation.expires_at.strftime("%Y-%m-%d %H:%M")}.
       Best regards, {invitation.company.name}
            ''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invitation.email],
            fail_silently=True,
        )

class CancelInvitationView(APIView):
    """
    Cancel a pending invitation (admin only).
    """
    permission_classes = [IsAuthenticated]
    def post(self, request, token):
        invitation = get_object_or_404(
            Invitation,
            token=token,
            company=request.user.company
        )

        if not request.user.is_company_admin:
            return Response({
                'error': 'Only company admin can cancel invitations.'
            }, status=403)

        if invitation.status != Invitation.STATUS_PENDING:
            return Response({
                'error': 'Can only cancel pending invitations.'
            }, status=400)

        invitation.status = Invitation.STATUS_CANCELLED
        invitation.save()

        return Response({'message': 'Invitation cancelled.'})


class ResendInvitationView(APIView):
    """
    Resend an invitation (admin only).
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, token):
        invitation = get_object_or_404(
            Invitation,
            token=token,
            company=request.user.company
        )

        if not request.user.is_company_admin:
            return Response({
                'error': 'Only company admin can resend invitations.'
            }, status=403)

        if invitation.status == Invitation.STATUS_ACCEPTED:
            return Response({
                'error': 'Cannot resend an accepted invitation.'
            }, status=400)

        invitation.expires_at = timezone.now() + timezone.timedelta(days=7)
        invitation.status = Invitation.STATUS_PENDING
        invitation.save()

        invite_url = f"{settings.FRONTEND_URL}/register?token={invitation.token}"

        send_mail(
            subject=f'Invitation Reminder - {invitation.company.name}',
            message=f"""Hello, This is a reminder about your invitation to join {invitation.company.name}. Click the link below to register: {invite_url}
            This invitation expires on {invitation.expires_at.strftime("%Y-%m-%d %H:%M")}.
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invitation.email],
            fail_silently=True,
              )

        return Response({'message': 'Invitation resent successfully.'})

class InvitationDetailView(APIView):
    """
        Get invitation details by token (for registration page).
    """
    permission_classes = [AllowAny]
    def get(self, request, token):
        try:
            invitation = Invitation.objects.filter(token=token, status=Invitation.STATUS_PENDING).first()

            if not invitation or invitation.is_expired:
                return Response({"error": "Invalid or expired invitation"}, status=400)

            serializer = InvitationDetailSerializer(invitation)
            return Response(serializer.data)

        except Invitation.DoesNotExist:
            return Response({"error": "Invalid token"}, status=404)
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
from rest_framework.exceptions import PermissionDenied,ValidationError
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from companies.utils import build_invitation_url
from django.conf import settings
from companies.models import Company
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from .models import User, Invitation, PasswordResetToken, UserProfile
from .serializers import (
    UserSerializer, UserDetailSerializer, UserUpdateSerializer,
    LoginSerializer, ChangePasswordSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    RegisterSerializer, CompanyRegistrationSerializer,
    InvitationSerializer, CreateInvitationSerializer,InvitationDetailSerializer,
    RegisterUserSerializer,RegisterWithInvitationSerializer
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
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                "message": "If this email exists, a reset link has been sent."
            })
        PasswordResetToken.objects.filter(user=user, used=False).delete()    
        #create new token
        reset_token = PasswordResetToken.objects.create(user=user)

        reset_url = f"{settings.FRONTEND_URL}/reset-password/{reset_token.token}"
        company_name = user.company.name if user.company else "PrintFlow"

        try:
            send_mail(
                subject=f'Password Reset - {company_name}',
                message=f'''Hello {user.get_full_name()}, You requested to reset your password. Click the following link:{reset_url} This link expires in 24 hours.
                If you did not request this, ignore this email.
                Best regards, {company_name}
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            return Response({
                "error": f"Email failed: {str(e)}"
            }, status=500)

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
        print("ERRORS:", serializer.errors) 
        if not serializer.is_valid():  
            return Response(serializer.errors, status=400)

        serializer.save()
        return Response({'message': 'Password reset successful. You can now login.'})


# =================
# REGISTRATION VIEWS
# ==================


#User registration views
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        company = getattr(request, "company", None)
        if not company:
            company_slug = request.data.get("company_slug")
            if company_slug:
                try:
                    company = Company.objects.get(slug=company_slug)
                except Company.DoesNotExist:
                    return Response(
                        {"error": "Invalid company slug"},
                        status=400
                    )

        if not company:
            return Response(
                {"error": "Invalid company context (missing subdomain or slug)"},
                status=400
            )

        serializer = RegisterUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        return Response({
            "user": UserSerializer(user).data,
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        }, status=201)
    
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
        from companies.models import Company, CompanySettings, CompanyInvitation

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # GET TOKEN FIRST
        token = request.data.get("token")
        if not token:
            return Response({'error': 'Invitation token is required'}, status=400)

        invitation = get_object_or_404(
            CompanyInvitation,
            token=token,
            status=CompanyInvitation.STATUS_PENDING
        )

        #  CHECK EXPIRY
        if invitation.expires_at < timezone.now():
            return Response({'error': 'Invitation expired'}, status=400)

        # PREVENT DUPLICATE ADMIN
        if User.objects.filter(
            role=User.ADMIN,
            company__slug=invitation.company_slug
        ).exists():
            return Response({'error': 'This company already has an admin.'}, status=400)

        # CREATE COMPANY
        company = Company.objects.create(
            name=data['company_name'],
            slug=invitation.company_slug,
            email=data['company_email'],
            phone=data['company_phone'],
            address=data['company_address'],
            city=data.get('company_city', ''),
            country=data.get('company_country', 'Kenya'),
        )

        CompanySettings.objects.create(company=company)

        #  CREATE ADMIN USER
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

        #  LINK ADMIN TO COMPANY
        company.admin = admin
        company.save()

        UserProfile.objects.get_or_create(user=admin)

        #  MARK INVITATION AS ACCEPTED (FIXED POSITION)
        invitation.status = CompanyInvitation.STATUS_ACCEPTED
        invitation.accepted_at = timezone.now()
        invitation.save()

        # GENERATE TOKENS
        refresh = RefreshToken.for_user(admin)
        invitation.status = CompanyInvitation.STATUS_ACCEPTED
        invitation.accepted_at = timezone.now()
        invitation.company = company
        invitation.save()  
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
            'message': f'Company "{company.name}" registered successfully!'
        }, status=status.HTTP_201_CREATED)
      



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
        user.delete()
        
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
class RegisterWithInvitationView(generics.CreateAPIView):
    serializer_class = RegisterWithInvitationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        return Response({
            "message": "User created successfully",
            "user_id": user.id
        }, status=201)
class InvitationListView(generics.ListCreateAPIView):
    """
    List and create invitations.
    Multi-tenant behavior:
    - Platform admin can view all invitations
    - Company admin can only view invitations within their company
    Invitation creation:
    - Platform admin can invite ONLY company admins
    - Company admin can invite designers, printers, and clients
    - Company is automatically assigned based on the inviter
    Email:
    - Sends an invitation link using company subdomain or custom domain
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return CreateInvitationSerializer if self.request.method == 'POST' else InvitationSerializer

    def get_queryset(self):
        user = self.request.user

        if user.role == "admin" and user.company:
            return Invitation.objects.filter(company=user.company).order_by('-created_at')

        return Invitation.objects.none()

    def perform_create(self, serializer):
        user = self.request.user

        if user.role != "admin":
            raise PermissionDenied("Only company admins can send invitations.")

        role = serializer.validated_data.get("role")

        if role == User.ADMIN:
            raise PermissionDenied("Company admin cannot invite another admin.")
        if user.role == "platform_admin":
            raise PermissionDenied("Platform admin cannot use this endpoint.")
        invitation = serializer.save(
            invited_by=user,
            company=user.company
        )

        invite_url = build_invitation_url(invitation)

        try:
            send_mail(
                subject=f'Invitation to join {invitation.company.name}',
                message=f"""
                Hello,
                You have been invited to join {invitation.company.name} as a {invitation.get_role_display()}.
                Click below to get started:
                {invite_url}
                This link expires on {invitation.expires_at.strftime("%Y-%m-%d %H:%M")}
                Best regards,  
                {invitation.company.name}
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[invitation.email],
                fail_silently=False,
                )
        except Exception as e:
            invitation.delete()
            raise ValidationError(f"Email failed: {str(e)}")

class CancelInvitationView(APIView):
    """
    Cancel a pending invitation (admin only).
    """
    permission_classes = [IsAuthenticated]
    def post(self, request, token):
        invitation = get_object_or_404(Invitation, token=token)

        if request.user.role == "admin" and invitation.company != request.user.company:
            return Response({"error": "Not allowed"}, status=403)

        user = request.user

        if user.role == "platform_admin":
            pass  

        elif user.role == "admin":
            if invitation.company != user.company:
                return Response({"error": "Not allowed"}, status=403)

        else:
            return Response({"error": "Not allowed"}, status=403)

        if invitation.status != Invitation.STATUS_PENDING:
            return Response({
                'error': 'Can only cancel pending invitations.'
            }, status=400)

        invitation.status = Invitation.STATUS_CANCELLED
        invitation.delete()

        return Response({'message': 'Invitation cancelled.'})

class ResendInvitationView(APIView):
    """
    Resend an invitation.

    Rules:
    - Platform admin can resend any invitation
    - Company admin can only resend invitations within their company
    - Cannot resend accepted invitations

    Behavior:
    - Resets expiration (7 days)
    - Keeps same token
    - Sends updated invitation link with correct domain/subdomain
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, token):
        invitation = get_object_or_404(Invitation, token=token)
        user = request.user

        # Permission checks
        if user.role == "platform_admin":
            pass
        elif user.role == "admin":
            if invitation.company != user.company:
                return Response({"error": "Not allowed"}, status=403)
        else:
            return Response({"error": "Not allowed"}, status=403)

        if invitation.status == Invitation.STATUS_ACCEPTED:
            return Response({
                'error': 'Cannot resend an accepted invitation.'
            }, status=400)

        # Reset invitation
        invitation.expires_at = timezone.now() + timedelta(days=7)
        invitation.status = Invitation.STATUS_PENDING
        invitation.accepted_at = None
        invitation.save()

        # Build domain-based URL
        invite_url = build_invitation_url(invitation)

        send_mail(
            subject=f'Invitation Reminder - {invitation.company.name}',
            message=f""" Hello, This is a reminder to join {invitation.company.name}. Click the link below to accept the invitation:{invite_url}
            This invitation expires on {invitation.expires_at.strftime("%Y-%m-%d %H:%M")}.
            Best regards, {invitation.company.name}
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invitation.email],
            fail_silently=False,
        )

        return Response({'message': 'Invitation resent successfully.'})

class InvitationDetailView(APIView):
    """
     Get invitation details by token (for registration page).
    """
    permission_classes = [AllowAny]

    def get(self, request, token):
        invitation = get_object_or_404(Invitation, token=token)

        # Force update status correctly
        if invitation.is_expired and invitation.status == Invitation.STATUS_PENDING:
            invitation.status = Invitation.STATUS_EXPIRED
            invitation.save(update_fields=["status"])

        serializer = InvitationDetailSerializer(invitation)
        return Response(serializer.data)

"""
All serializers for user management, authentication, and invitations.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone

from .models import Invitation, PasswordResetToken, UserProfile, User
from companies.models import Company

User = get_user_model()


# =====================
# USER SERIALIZERS
# =====================

class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer."""
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'role_display', 'avatar', 'phone',
            'company', 'company_name',
            'email_verified', 'created_at'
        ]
        read_only_fields = ['id', 'email', 'role', 'company', 'email_verified', 'created_at']


class UserProfileSerializer(serializers.ModelSerializer):
    """Extended user profile serializer."""
    
    class Meta:
        model = UserProfile
        fields = [
            'bio', 'company_name', 'company_address',
            'website', 'linkedin',
            'total_orders', 'completed_jobs', 'total_spent',
        ]


class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed user serializer with profile."""
    
    profile = UserProfileSerializer(read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'role_display', 'avatar', 'phone', 'address',
            'company', 'company_name',
            'email_verified', 'created_at', 'updated_at',
            'profile'
        ]
        read_only_fields = ['id', 'email', 'role', 'company', 'email_verified', 'created_at']


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'address', 'avatar']

# =====================
# AUTHENTICATION SERIALIZERS
# =====================

class LoginSerializer(serializers.Serializer):
    """User login serializer."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class ChangePasswordSerializer(serializers.Serializer):
    """Change password serializer."""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "Passwords do not match."})
        return attrs
    
    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """Password reset request serializer."""
    
    email = serializers.EmailField()
    
    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "No user found with this email address.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Password reset confirmation serializer."""
    
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate_token(self, value):
        try:
            reset_token = PasswordResetToken.objects.get(token=value)
            if not reset_token.is_valid:
                raise serializers.ValidationError("This reset token has expired or been used.")
            return reset_token
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError("Invalid reset token.")
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "Passwords do not match."})
        return attrs
    
    def save(self):
        reset_token_obj = self.validated_data['token']
        user = reset_token_obj.user

        user.set_password(self.validated_data['new_password'])
        user.save()

        reset_token_obj.mark_used()
        return user


# =====================
# REGISTRATION SERIALIZERS
# =====================

class RegisterSerializer(serializers.ModelSerializer):
    """
    User registration via invitation.
    Used when accepting invitation to join a company.
    """
    
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    invitation_token = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'password', 'password_confirm', 'invitation_token',
            'first_name', 'last_name', 'phone'
        ]
    
    def validate_invitation_token(self, value):
        try:
            invitation = Invitation.objects.get(token=value)

            if invitation.status != Invitation.STATUS_PENDING:
                raise serializers.ValidationError("Invitation already used.")

            if invitation.is_expired:
                raise serializers.ValidationError("Invitation has expired.")

            return invitation

        except Invitation.DoesNotExist:
            raise serializers.ValidationError("Invalid invitation token.")
    
    def validate_email(self, value):
        value = value.lower()

        invitation_token = self.initial_data.get('invitation_token')

        try:
            invitation = Invitation.objects.get(token=invitation_token)

            if invitation.email.lower() != value:
                raise serializers.ValidationError(
                    f"Email must match invitation: {invitation.email}"
                )
        except Invitation.DoesNotExist:
            pass

        return value
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs
    
    def create(self, validated_data):
        invitation = validated_data.pop('invitation_token')
        validated_data.pop('password_confirm')
        
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone=validated_data.get('phone', ''),
            email_verified=True,
        )

        invitation.accept(user)
        UserProfile.objects.get_or_create(user=user)
        
        return user


class CompanyRegistrationSerializer(serializers.Serializer):
    """
    Company registration serializer.
    Creates a new company and its admin user.
    
    """
    
    # Company fields
    company_name = serializers.CharField(max_length=200)
    company_slug = serializers.SlugField(max_length=200)
    company_email = serializers.EmailField()
    company_phone = serializers.CharField(max_length=20)
    company_address = serializers.CharField()
    company_city = serializers.CharField(max_length=100, required=False, default='')
    company_country = serializers.CharField(max_length=100, required=False, default='Kenya')
    
    # Admin fields
    admin_first_name = serializers.CharField(max_length=150)
    admin_last_name = serializers.CharField(max_length=150)
    admin_email = serializers.EmailField()
    admin_password = serializers.CharField(validators=[validate_password])
    admin_phone = serializers.CharField(max_length=20, required=False, default='')
    
    def validate_company_slug(self, value):
        if Company.objects.filter(slug=value).exists():
            raise serializers.ValidationError("This company slug is already taken.")
        return value
    
    def validate_company_email(self, value):
        if Company.objects.filter(email=value).exists():
            raise serializers.ValidationError("A company with this email already exists.")
        return value
    
    def validate_admin_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    def validate(self, attrs):
        if User.objects.filter(
            company__slug=attrs.get('company_slug'),
            role=User.ADMIN
        ).exists():
            raise serializers.ValidationError(
                "This company already has an admin."
            )
        return attrs
    def create(self, validated_data):
        company = Company.objects.create(
            name=validated_data['company_name'],
            slug=validated_data['company_slug'],
            email=validated_data['company_email'],
            phone=validated_data['company_phone'],
            address=validated_data['company_address'],
            city=validated_data.get('company_city', ''),
            country=validated_data.get('company_country', 'Kenya'),
        )

        admin = User.objects.create_user(
            email=validated_data['admin_email'],
            password=validated_data['admin_password'],
            first_name=validated_data['admin_first_name'],
            last_name=validated_data['admin_last_name'],
            phone=validated_data.get('admin_phone', ''),
            role=User.ADMIN,
            company=company,
            email_verified=True
        )

        UserProfile.objects.get_or_create(user=admin)

        return {
            "company": company,
            "admin": admin
        }                


# =====================
# INVITATION SERIALIZERS
# =====================

class InvitationSerializer(serializers.ModelSerializer):
    """Invitation serializer."""
    
    invited_by_name = serializers.CharField(source='invited_by.get_full_name', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_valid = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Invitation
        fields = [
            'id', 'token', 'email', 'role', 'role_display',
            'invited_by', 'invited_by_name',
            'company', 'company_name',
            'message', 'status', 'status_display',
            'is_valid', 'is_expired',
            'created_at', 'expires_at', 'accepted_at'
        ]
        read_only_fields = [
            'id', 'token', 'invited_by', 'company', 'status',
            'created_at', 'expires_at', 'accepted_at'
        ]


class CreateInvitationSerializer(serializers.ModelSerializer):
    """Serializer for creating invitations (admin only)."""
    
    class Meta:
        model = Invitation
        fields = ['email', 'role', 'message']
    
    def validate_role(self, value):
        if value not in [User.DESIGNER, User.PRINTER, User.CLIENT]:
            raise serializers.ValidationError(
                "Can only invite designer, printer, or client."
            )
        return value
    
    def validate_email(self, value):
        request = self.context.get('request')
        if request and request.user.company:
            if User.objects.filter(
                email=value,
                company=request.user.company
            ).exists():
                raise serializers.ValidationError(
                    "A user with this email already exists in your company."
                )
    def create(self, validated_data):
        request = self.context['request']

        validated_data['invited_by'] = request.user
        validated_data['company'] = request.user.company

        return super().create(validated_data)

        if Invitation.objects.filter(
            email=value,
            company=request.user.company,
            status=Invitation.STATUS_PENDING).exists():
            raise serializers.ValidationError(
                "A pending invitation already exists for this email."
            )
        
        return value

class InvitationDetailSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = Invitation
        fields = ['email', 'company_name', 'role', 'role_display', 'is_valid']
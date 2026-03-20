"""
Account Serializers - User, Invitation, Authentication
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from .models import Invitation, PasswordResetToken, UserProfile

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Basic user serializer
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'avatar', 'phone', 'address',
            'company', 'company_name',
            'email_verified', 'created_at'
        ]
        read_only_fields = ['id', 'email', 'role', 'company', 'email_verified', 'created_at']

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Extended user profile serializer
    """
    class Meta:
        model = UserProfile
        fields = [
            'bio', 'company_name', 'company_address',
            'website', 'linkedin',
            'notification_preferences'
        ]        

class UserDetailSerializer(serializers.ModelSerializer):
    """
    Detailed user serializer with profile
    """
    profile = UserProfileSerializer(read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'avatar', 'phone', 'address',
            'company', 'company_name',
            'email_verified', 'created_at', 'updated_at',
            'profile'
        ]
        read_only_fields = ['id', 'email', 'role', 'company', 'email_verified', 'created_at']

class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'address', 'avatar']

class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration via invitation
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
            if not invitation.is_valid:
                raise serializers.ValidationError("This invitation is no longer valid.")
            return invitation
        except Invitation.DoesNotExist:
            raise serializers.ValidationError("Invalid invitation token.")
    
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
            role=invitation.role,
            company=invitation.company,
            email_verified=True,
            email_verified_at=timezone.now(),
        )
        
        # Accept the invitation
        invitation.accept(user)
        
        # Create profile
        UserProfile.objects.get_or_create(user=user)
        
        return user        
class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing password
    """
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
    """
    Serializer for requesting password reset
    """
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            return user
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address.")
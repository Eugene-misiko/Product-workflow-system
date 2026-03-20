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
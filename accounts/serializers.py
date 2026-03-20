from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.core.exceptions import ValidationError
import base64
from django.utils.encoding import force_str

class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer used for registering a new user.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "password",
            "role"
        ]

    def create(self, validated_data):
        role = validated_data.get("role", User.CLIENT)

        user = User.objects.create_user(
            first_name=validated_data["first_name"],
            email=validated_data["email"],
            phone=validated_data.get("phone"),
            last_name=validated_data.get("last_name"),
            password=validated_data["password"],
            role=role,   
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)



# PASSWORD CHANGE (For Logged In Users)

class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change endpoint (User is already logged in).
    """
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True, required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct.")
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


# PASSWORD RESET (Forgot Password Flow)

class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting a password reset link (via Email).
    """
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        # check if user exists. 
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value




class PasswordResetConfirmSerializer(serializers.Serializer):
    uidb64 = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        # 1. Check passwords match
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})

        # 2. Decode User ID
        try:
            # Django's urlsafe_base64_decode handles padding internally automatically
            uid = force_str(urlsafe_base64_decode(attrs['uidb64']))
            self.user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
            # If any error occurs here, the link is invalid
            raise serializers.ValidationError({"uidb64": "Invalid reset link."})

        # 3. Check Token
        if not default_token_generator.check_token(self.user, attrs['token']):
            raise serializers.ValidationError({"token": "Invalid or expired reset link."})

        return attrs

    def save(self, **kwargs):
        self.user.set_password(self.validated_data['new_password'])
        self.user.save()
        return self.user



# USER PROFILE

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for viewing or updating user profile.
    """
    # Allow avatar to be optional during updates
    avatar = serializers.ImageField(required=False, allow_null=True)
    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "email", "phone", "role", "avatar")
        read_only_fields = ("role", "email") 

    def update(self, instance, validated_data):
        # Handle standard fields
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.phone = validated_data.get('phone', instance.phone)
        
        # Handle file upload specifically if needed 
        if 'avatar' in validated_data:
            instance.avatar = validated_data['avatar']
            
        instance.save()
        return instance
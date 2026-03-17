from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password

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


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for viewing or updating user profile.
    """
    avatar = serializers.ImageField(required=False)

    class Meta:
        model = User
        fields = ("id", "first_name", "email", "phone", "role", "avatar", "last_name")
        read_only_fields = ("role",)
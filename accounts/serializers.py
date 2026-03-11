from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password

class RegisterSerializer(serializers.ModelSerializer):
    
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
        ]

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            phone=validated_data.get("phone"),
            first_name=validated_data.get("first_name"),
            last_name=validated_data.get("last_name"),
            password=validated_data["password"],
        )

        user.role = User.CLIENT
        user.save()

        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for viewing or updating user profile.
    """

    class Meta:
        model = User
        fields = ("id", "first_name", "email", "phone", "role")
        read_only_fields = ("role",)



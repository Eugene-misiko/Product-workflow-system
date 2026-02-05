from rest_framework import serializers
from .models import User

class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer used for client registration.
    """

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("username", "email", "phone", "password")

    def create(self, validated_data):
        """
        Create a new client user.
        """
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            phone=validated_data.get("phone"),
            password=validated_data["password"],
            role=User.CLIENT
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for viewing or updating user profile.
    """

    class Meta:
        model = User
        fields = ("id", "username", "email", "phone", "role")
        read_only_fields = ("role",)



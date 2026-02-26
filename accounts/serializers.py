from rest_framework import serializers
from .models import User

class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for registering new users with selectable roles.
    """

    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(
        choices=[User.CLIENT, User.DESIGNER, User.ADMIN],
        default=User.CLIENT
    )

    class Meta:
        model = User
        fields = ("username", "email", "phone", "password", "role")

    def create(self, validated_data):
        """
        Create a new user with the specified role.
        """
        role = validated_data.pop("role", User.CLIENT)
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            phone=validated_data.get("phone"),
            password=validated_data["password"],
            role=role
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



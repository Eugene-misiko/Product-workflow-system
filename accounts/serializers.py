from rest_framework import serializers
from .models import User

class RegisterSerializer(serializers.ModelSerializer):
    """
    Secure serializer for registering new users.
    All new users are automatically assigned the CLIENT role.
    """

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("username", "email", "phone", "password")
        extra_kwargs = {
            "password": {"write_only": True}
        }

    def create(self, validated_data):
        """
        Create a new user and force role to CLIENT.
        """
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            phone=validated_data.get("phone"),
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
        fields = ("id", "username", "email", "phone", "role")
        read_only_fields = ("role",)



from rest_framework import serializers

from users.models import User
from users.validators import PhoneNumberValidator, UsernameValidator


class UserCreateSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(
        required=True,
        validators=[PhoneNumberValidator()],  # type: ignore
    )
    username = serializers.CharField(required=False, validators=[UsernameValidator()])

    class Meta:
        model = User
        fields = [
            "id",
            "created_at",
            "updated_at",
            "username",
            "phone_number",
            "password",
            "is_active",
            "is_verified",
            "is_staff",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "username": {"required": False},
            "password": {"write_only": True},
        }


class BaseUserUpdateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False, validators=[UsernameValidator()])

    class Meta:
        model = User
        fields = ["username", "is_active", "is_verified", "is_staff"]


class UserUpdateSerializer(BaseUserUpdateSerializer):
    class Meta(BaseUserUpdateSerializer.Meta):
        read_only_fields = ("is_active", "is_verified", "is_staff")


class AdminUserUpdateSerializer(BaseUserUpdateSerializer):
    class Meta(BaseUserUpdateSerializer.Meta):
        """Admin can edit any of the fields"""

        read_only_fields = ()

from rest_framework import serializers

from users.models import User
from users.validators import PhoneNumberValidator, UsernameValidator


class UserSerializer(serializers.ModelSerializer):
    """User fields required when making a request."""

    phone_number = serializers.CharField(
        required=True,
        validators=[PhoneNumberValidator()],  # type: ignore
    )
    username = serializers.CharField(required=False, validators=[UsernameValidator()])  # type: ignore

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

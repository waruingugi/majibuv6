from phonenumbers import PhoneNumberFormat, format_number
from phonenumbers import parse as parse_phone_number
from rest_framework import serializers

from commons.constants import DEFAULT_COUNTRY_CODE
from users.models import User
from users.validators import PhoneNumberValidator, UsernameValidator


class UserCreateSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(
        required=True, validators=[PhoneNumberValidator()]
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

    def validate_phone_number(self, phone):
        """Change phone number input to international format: +254702005008"""
        try:
            parsed_phone = parse_phone_number(phone, DEFAULT_COUNTRY_CODE)

            return format_number(parsed_phone, PhoneNumberFormat.E164)
        except Exception:
            raise serializers.ValidationError("This phone number is not valid.")


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

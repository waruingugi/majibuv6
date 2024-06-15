from django.contrib.auth.password_validation import validate_password
from phonenumbers import PhoneNumberFormat, format_number, parse
from rest_framework import serializers

from users.constants import DEFAULT_COUNTRY_CODE
from users.models import User
from users.validators import PhoneNumberValidator, UsernameValidator


class UserCreateSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(
        required=True, validators=[PhoneNumberValidator()]
    )
    username = serializers.CharField(required=False, validators=[UsernameValidator()])
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],  # Use Django's built-in validators
    )

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

    def validate_phone_number(self, phone):
        """Change phone number input to international format: +254702005008"""
        try:
            parsed_phone = parse(phone, DEFAULT_COUNTRY_CODE)

            return format_number(parsed_phone, PhoneNumberFormat.E164)
        except Exception:
            raise serializers.ValidationError("This phone number is not valid.")


class BaseUserDetailSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False, validators=[UsernameValidator()])

    class Meta:
        model = User
        fields = [
            "id",
            "created_at",
            "updated_at",
            "username",
            "phone_number",
            "is_active",
            "is_verified",
            "is_staff",
        ]


class UserRetrieveUpdateSerializer(BaseUserDetailSerializer):
    class Meta(BaseUserDetailSerializer.Meta):
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "is_active",
            "phone_number",
            "is_verified",
            "is_staff",
        )


class StaffUserRetrieveUpdateSerializer(BaseUserDetailSerializer):
    class Meta(BaseUserDetailSerializer.Meta):
        """Staff can edit any of the fields except those specified below."""

        read_only_fields = ("id", "created_at", "updated_at")


class UserListSerializer(BaseUserDetailSerializer):
    class Meta(BaseUserDetailSerializer.Meta):
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "username",
            "phone_number",
            "is_active",
            "is_verified",
            "is_staff",
        ]

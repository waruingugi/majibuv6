from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from commons.serializers import UserPhoneNumberField
from users.models import User
from users.validators import (
    OTPValidator,
    PhoneNumberExistsValidator,
    PhoneNumberIsAvailableValidator,
    UsernameValidator,
)


class UserCreateSerializer(serializers.ModelSerializer):
    phone_number = UserPhoneNumberField(
        required=True, validators=[PhoneNumberIsAvailableValidator()]
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


class UserReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "username",
            "phone_number",
        ]


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

        read_only_fields = ("id", "created_at", "updated_at", "phone_number")


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


class OTPVerificationSerializer(serializers.Serializer):
    phone_number = UserPhoneNumberField(required=True)
    otp = serializers.CharField(required=True, max_length=6)

    def validate(self, data):
        OTPValidator.validate_otp(
            phone_number=data.get("phone_number"), otp_code=data.get("otp")
        )
        return data


class UserTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        """Change phone number to standard format"""
        phone_field = UserPhoneNumberField()
        # Username is phone number field(as specified in User model)
        attrs[self.username_field] = phone_field.to_internal_value(
            attrs[self.username_field]
        )
        data = super().validate(attrs)
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    phone_number = UserPhoneNumberField(
        required=True, validators=[PhoneNumberExistsValidator()]
    )


class PasswordResetConfirmSerializer(serializers.Serializer):
    phone_number = UserPhoneNumberField(
        required=True, validators=[PhoneNumberExistsValidator()]
    )
    otp = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True, write_only=True, validators=[validate_password]
    )

    def validate(self, data):
        OTPValidator.validate_otp(
            phone_number=data.get("phone_number"), otp_code=data.get("otp")
        )
        return data

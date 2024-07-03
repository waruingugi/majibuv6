from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from commons.errors import ErrorCodes
from commons.serializers import UserPhoneNumberField
from users.constants import TOTP_LENGTH
from users.models import User
from users.validators import (
    OTPValidator,
    PhoneNumberExistsValidator,
    PhoneNumberIsAvailableValidator,
    UsernameValidator,
)


class BaseUserCreateSerializer(serializers.ModelSerializer):
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


class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = [
            "id",
            "username",
            "phone_number",
            "password",
            "is_active",
            "is_verified",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
            "username": {"read_only": True},
            "is_active": {"read_only": True},
            "is_verified": {"read_only": True},
            "password": {"write_only": True},
        }


class StaffUserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
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
        extra_kwargs = {
            "id": {"read_only": True},
            "created_at": {"read_only": True},
            "updated_at": {"read_only": True},
            "password": {"write_only": True},
        }


# class UserCreateSerializer(serializers.ModelSerializer):
#     phone_number = UserPhoneNumberField(
#         required=True, validators=[PhoneNumberIsAvailableValidator()]
#     )
#     username = serializers.CharField(required=False, validators=[UsernameValidator()])
#     password = serializers.CharField(
#         write_only=True,
#         required=True,
#         validators=[validate_password],  # Use Django's built-in validators
#     )

#     class Meta:
#         model = User
#         fields = [
#             "id",
#             "created_at",
#             "updated_at",
#             "username",
#             "phone_number",
#             "password",
#             "is_active",
#             "is_verified",
#             "is_staff",
#         ]
#         read_only_fields = ["id", "created_at", "updated_at"]


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


class ResendOTPVerificationSerializer(serializers.Serializer):
    phone_number = UserPhoneNumberField(
        required=True, validators=[PhoneNumberExistsValidator()]
    )

    def validate(self, data):
        user = User.objects.get(phone_number=data["phone_number"])
        if user.is_verified:
            raise serializers.ValidationError(ErrorCodes.USER_IS_VERIFIED.value)
        return data


class OTPVerificationSerializer(serializers.Serializer):
    phone_number = UserPhoneNumberField(
        required=True, validators=[PhoneNumberExistsValidator()]
    )
    otp = serializers.CharField(required=True, max_length=TOTP_LENGTH)

    def validate(self, data):
        OTPValidator.validate_otp(
            phone_number=data.get("phone_number"), otp_code=data.get("otp")
        )
        return data


class UserTokenObtainPairSerializer(TokenObtainPairSerializer):
    default_error_messages = {
        "no_active_account": _(ErrorCodes.INCORRECT_USERNAME_OR_PASSWORD.value)
    }

    def validate(self, attrs):
        """Change phone number to standard format"""
        phone_field = UserPhoneNumberField()
        # Username is phone number field(as specified in User model)
        attrs[self.username_field] = phone_field.to_internal_value(
            attrs[self.username_field]
        )
        data = super().validate(attrs)
        data["id"] = self.user.id  # type: ignore
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

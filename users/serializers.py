from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from phonenumbers import (
    NumberParseException,
    PhoneNumberFormat,
    PhoneNumberType,
    format_number,
    is_valid_number,
    number_type,
)
from phonenumbers import parse as parse_phone_number
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from users.constants import DEFAULT_COUNTRY_CODE
from users.models import User
from users.validators import (
    OTPValidator,
    PhoneNumberExistsValidator,
    PhoneNumberIsAvailableValidator,
    UsernameValidator,
)


class UserPhoneNumberField(serializers.CharField):
    default_error_messages = {"invalid": _("This phone number is not valid")}

    def __init__(self, *args, region=None, **kwargs) -> None:
        """
        :keyword str region: 2-letter country code as defined in ISO 3166-1.
            When not supplied, defaults to :setting:`PHONENUMBER_DEFAULT_REGION`
        """
        super().__init__(*args, **kwargs)
        self.region = region or DEFAULT_COUNTRY_CODE

    def to_internal_value(self, phone_number) -> str:
        """Format the phone number to international format: +254732567432"""
        PHONE_NUMBER_TYPES = (
            PhoneNumberType.MOBILE,
            PhoneNumberType.FIXED_LINE_OR_MOBILE,
        )

        try:
            phone_number = parse_phone_number(phone_number, self.region)
        except NumberParseException:
            raise serializers.ValidationError(self.error_messages["invalid"])

        if number_type(phone_number) not in PHONE_NUMBER_TYPES or not is_valid_number(
            phone_number
        ):
            raise serializers.ValidationError(self.error_messages["invalid"])

        return format_number(phone_number, PhoneNumberFormat.E164)


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
    phone_number = UserPhoneNumberField(
        required=True, validators=[PhoneNumberExistsValidator()]
    )


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

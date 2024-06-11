from phonenumbers import (
    NumberParseException,
    PhoneNumberFormat,
    PhoneNumberType,
    format_number,
    is_valid_number,
    number_type,
)
from phonenumbers import parse
from phonenumbers import parse as parse_phone_number
from rest_framework import serializers

from commons.constants import MAX_USERNAME_LEN, MIN_USERNAME_LEN
from users.models import User


class PhoneNumberValidator:
    def __init__(self) -> None:
        self.default_country_code = "KE"

    def __call__(self, phone) -> str | None:
        """Run phone number validation checks."""
        self.validate_phone_number(phone)
        return self.standardize_phone_to_required_format(phone)

    def validate_phone_number(self, phone: str) -> None:
        """Validate str can be parsed into phone number"""
        PHONE_NUMBER_TYPES = (
            PhoneNumberType.MOBILE,
            PhoneNumberType.FIXED_LINE_OR_MOBILE,
        )

        try:
            parsed_phone = parse_phone_number(phone, self.default_country_code)
        except NumberParseException:
            raise serializers.ValidationError("This phone number is not valid.")

        if number_type(parsed_phone) not in PHONE_NUMBER_TYPES or not is_valid_number(
            parsed_phone
        ):
            raise serializers.ValidationError("This phone number is not valid.")

    def standardize_phone_to_required_format(self, phone: str) -> str | None:
        """Change phone number input to international format: +254702005008"""
        try:
            parsed_phone = parse(phone, self.default_country_code)

            return format_number(parsed_phone, PhoneNumberFormat.E164)
        except Exception:
            raise serializers.ValidationError(
                "This phone number does not belong to any country."
            )


class UsernameValidator:
    def __init__(
        self, minimum_length=MIN_USERNAME_LEN, max_length=MAX_USERNAME_LEN
    ) -> None:
        self.max_len = max_length
        self.min_len = minimum_length

    def __call__(self, username) -> str | None:
        if len(username) < self.min_len:
            raise serializers.ValidationError("This username is too short.")

        if len(username) > self.max_len:
            raise serializers.ValidationError("This username is too long.")

        if not username.isalnum():
            raise serializers.ValidationError(
                "Username can contain letters[a-z] and numbers[0-9]."
            )

        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError("This username is already taken.")

        return username

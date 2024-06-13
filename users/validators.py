from phonenumbers import (
    NumberParseException,
    PhoneNumberType,
    is_valid_number,
    number_type,
)
from phonenumbers import parse as parse_phone_number
from rest_framework import serializers

from users.constants import DEFAULT_COUNTRY_CODE, MAX_USERNAME_LEN, MIN_USERNAME_LEN
from users.models import User


class PhoneNumberValidator:
    def __call__(self, phone) -> None:
        """Validate str can be parsed into phone number"""
        PHONE_NUMBER_TYPES = (
            PhoneNumberType.MOBILE,
            PhoneNumberType.FIXED_LINE_OR_MOBILE,
        )

        try:
            parsed_phone = parse_phone_number(phone, DEFAULT_COUNTRY_CODE)
        except NumberParseException:
            raise serializers.ValidationError("This phone number is not valid.")

        if number_type(parsed_phone) not in PHONE_NUMBER_TYPES or not is_valid_number(
            parsed_phone
        ):
            raise serializers.ValidationError("This phone number is not valid.")

        if User.objects.filter(phone_number=phone).exists():
            raise serializers.ValidationError("This phone number is already taken.")


class UsernameValidator:
    def __init__(
        self, minimum_length=MIN_USERNAME_LEN, max_length=MAX_USERNAME_LEN
    ) -> None:
        self.max_len = max_length
        self.min_len = minimum_length

    def __call__(self, username) -> None:
        if len(username) < self.min_len:
            raise serializers.ValidationError("This username is too short.")

        if len(username) > self.max_len:
            raise serializers.ValidationError("This username is too long.")

        if not username.isalnum():
            raise serializers.ValidationError(
                "Username can only contain letters[a-z] and numbers[0-9]."
            )

        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError("This username is already taken.")

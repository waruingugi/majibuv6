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


class PhoneNumberValidator:
    def __init__(self) -> None:
        self.default_country_code = "KE"

    def __call__(self, phone):
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

    def standardize_phone_to_required_format(self, phone: str):
        """Change phone number input to international format: +254702005008"""
        try:
            parsed_phone = parse(phone, self.default_country_code)

            return format_number(parsed_phone, PhoneNumberFormat.E164)
        except Exception:
            raise serializers.ValidationError(
                "This phone number does not belong to any country."
            )

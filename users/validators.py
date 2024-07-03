from rest_framework import serializers

from commons.errors import ErrorCodes
from users.constants import MAX_USERNAME_LEN, MIN_USERNAME_LEN
from users.models import User
from users.otp import validate_otp


class PhoneNumberIsAvailableValidator:
    def __call__(self, phone) -> None:
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


class PhoneNumberExistsValidator:
    def __call__(self, phone_number) -> None:
        if not User.objects.filter(phone_number=phone_number).exists():
            raise serializers.ValidationError("This user does not exist")


class OTPValidator:
    @staticmethod
    def validate_otp(phone_number: str, otp_code: str) -> None:
        if not validate_otp(otp_code, phone_number):
            raise serializers.ValidationError(ErrorCodes.INVALID_OTP.value)

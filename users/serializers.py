from random_username.generate import generate_username
from rest_framework import serializers

from users.models import User
from users.utils import PhoneNumberValidator


class UserSerializer(serializers.ModelSerializer):
    """User fields required when making a request."""

    phone_number = serializers.CharField(
        required=True, validators=[PhoneNumberValidator()]
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
        extra_kwargs = {
            "username": {"required": False},
            "password": {"write_only": True},
        }

    def validate_username(self, username):
        """Assert that the username is unique"""

        if username is None or username.strip() == "":
            # Generate a username
            username = generate_username(1)[0]
            while User.objects.filter(username=username).exists():
                username = generate_username(1)[0]
            return username

        else:
            if len(username) > 15:
                raise serializers.ValidationError("This username is too long")
            # Check if the provided username is unique
            if User.objects.filter(username=username).exists():
                raise serializers.ValidationError("This username is already taken.")
            return username

    def validate_phone_number(self, phone_number):
        """Phone number can not be updated once user is created"""
        validator = PhoneNumberValidator()
        return validator(phone_number)

        # if self.instance and phone_number != self.instance.phone_number:
        #     raise serializers.ValidationError("Phone number can not be edited.")
        # return phone_number

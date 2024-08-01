from enum import Enum

from django.conf import settings


class ErrorCodes(str, Enum):
    BUSINESS_IS_CLOSED = (
        "Oh, you just missed the party!"
        "Please check in again between "
        f"{settings.BUSINESS_OPENS_AT}a.m. "
        "and "
        f"{settings.BUSINESS_CLOSES_AT}p.m. "
        "to play a session."
    )
    CONTEXT_IS_REQUIRED = "Request context is required for validation."
    INCORRECT_USERNAME_OR_PASSWORD = (
        "The phone number or password is incorrect. Please try again."
    )
    INVALID_OTP = "The OTP entered is incorrect. Please try again"
    INVALID_PHONE_NUMBER = "This phone number is incorrect. Please try again."
    INVALID_SESSION_ID = (
        "The session you requested is invalid or has expired. Please try again."
    )
    INSUFFICIENT_BALANCE_TO_WITHDRAW = (
        "You do not have sufficient balance to withdraw Ksh {}. "
        "Please check withdrawal fees."
    )
    NO_AVAILABLE_SESSION = (
        "There are no available sessions at this time. " "Please try again later."
    )
    PHONE_NUMBER_EXISTS = "This phone number is already taken."
    SESSION_IN_QUEUE = (
        "Your previous session is still being processed. Please try again later."
    )
    SIMILAR_WITHDRAWAL_REQUEST = (
        "A similar withdrawal request for ksh {} is currently being processed."
    )
    USERNAME_EXISTS = "This username is already taken."
    USERNAME_IS_INVALID = "Username can only contain letters[a-z] and numbers[0-9]."
    USERNAME_IS_TOO_SHORT = "This username is too short."
    USERNAME_IS_TOO_LONG = "This username is too long."
    USER_IS_VERIFIED = "This user is already verified."
    USER_DOES_NOT_EXIST = "This user does not exist"
    WITHDRAWAL_REQUEST_IN_QUEUE = "Your previous withdrawal request is still being processed. Please try again in a few minutes."

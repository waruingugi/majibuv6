from enum import Enum


class ErrorCodes(str, Enum):
    INCORRECT_USERNAME_OR_PASSWORD = (
        "The phone number or password is incorrect. " "Please try again."
    )
    INVALID_OTP = "The OTP entered is incorrect. Please try again"
    INVALID_PHONE_NUMBER = "This phone number is incorrect. Please try again."
    PHONE_NUMBER_EXISTS = "This phone number is already taken."
    USERNAME_EXISTS = "This username is already taken."
    USERNAME_IS_TOO_SHORT = "This username is too short."
    USERNAME_IS_TOO_LONG = "This username is too long."
    USER_IS_VERIFIED = "This user is already verified."
    USER_DOES_NOT_EXIST = "This user does not exist"

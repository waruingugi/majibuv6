from enum import Enum


class ErrorCodes(str, Enum):
    INCORRECT_USERNAME_OR_PASSWORD = (
        "The phone number or password is incorrect. Please try again."
    )
    INVALID_OTP = "The OTP entered is incorrect. Please try again"
    INVALID_PHONE_NUMBER = "This phone number is incorrect. Please try again."
    INSUFFICIENT_BALANCE_TO_WITHDRAW = (
        "You do not have sufficient balance to withdraw Ksh {}. "
        "Please check withdrawal fees."
    )
    PHONE_NUMBER_EXISTS = "This phone number is already taken."
    SIMILAR_WITHDRAWAL_REQUEST = (
        "A similar withdrawal request for ksh {} is currently being processed."
    )
    USERNAME_EXISTS = "This username is already taken."
    USERNAME_IS_INVALID = "Username can only contain letters[a-z] and numbers[0-9]."
    USERNAME_IS_TOO_SHORT = "This username is too short."
    USERNAME_IS_TOO_LONG = "This username is too long."
    USER_IS_VERIFIED = "This user is already verified."
    USER_DOES_NOT_EXIST = "This user does not exist"

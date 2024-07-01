from enum import Enum


class ErrorCodes(str, Enum):
    INCORRECT_USERNAME_OR_PASSWORD = (
        "The phone number or password is incorrect. " "Please try again."
    )

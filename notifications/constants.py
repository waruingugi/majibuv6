from enum import Enum


class NotificationChannels(str, Enum):
    SMS = "SMS"
    PUSH = "PUSH"


class NotificationProviders(str, Enum):
    HOSTPINNACLESMS = "HOSTPINNACLESMS"
    ONESIGNAL = "ONESIGNAL"


class NotificationTypes(str, Enum):
    OTP = "OTP"
    MARKETING = "MARKETING"
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"
    SESSION = "SESSION"


class Messages(str, Enum):
    OTP_SMS = "Your Majibu verification code is {}."
    WELCOME_MESSAGE = "Welcome to Majibu! Please top up your account to start playing."


class PushNotifications:
    class WELCOME_MESSAGE:
        title = "Welcome to Majibu"
        message = (
            "We're excited you joined us! Please top up your account to start playing."
        )

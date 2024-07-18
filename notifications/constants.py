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
    WELCOME_MESSAGE = (
        "Hello and welcome to Majibu! Please top up your wallet to start playing."
    )


class PushNotifications:
    class WELCOME_MESSAGE:
        title = "Welcome to Majibu"
        message = (
            "Hello and welcome to Majibu! Please top up your wallet to start playing."
        )

    class MPESA_DEPOSIT:
        title = "Funds added to your wallet."
        message = (
            "You've successfully deposited Ksh{} for your account {}. "
            "New balance is Ksh{}. "
            "Thank your for choosing Majibu!"
        )

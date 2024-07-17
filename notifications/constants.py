from enum import Enum

from notifications.push import OneSignal
from notifications.sms import HostPinnacleSMS

SMS_PROVIDERS = [HostPinnacleSMS]
PUSH_PROVIDERS = [OneSignal]


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


class NotificationMessages(str, Enum):
    OTP_SMS = "Your Majibu verification code is {}."
    WELCOME_MESSAGE = "Welcome to Majibu! Please top up your account to start playing."

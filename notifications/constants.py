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
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"
    SESSION = "SESSION"

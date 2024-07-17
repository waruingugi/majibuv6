from enum import Enum

from notifications.sms import HostPinnacleSMS

SMS_PROVIDERS = [HostPinnacleSMS]


class NotificationChannels(str, Enum):
    SMS = "SMS"
    PUSH = "PUSH"


class NotificationTypes(str, Enum):
    OTP = "OTP"
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"
    SESSION = "SESSION"


class NotificationStatuses(str, Enum):
    CREATED = "CREATED"
    PENDING = "PENDING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"

from enum import Enum

from django.contrib.auth import get_user_model

from notifications.push import OneSignal
from notifications.sms import HostPinnacleSMS

# Notification Providers
SMS_PROVIDERS = [HostPinnacleSMS]
PUSH_PROVIDERS = [OneSignal]


# Model Constants
User = get_user_model()

SESSION_RESULT_DECIMAL_PLACES: int = 7
MONETARY_DECIMAL_PLACES: int = 2


# Model Choices
class SessionCategories(str, Enum):
    FOOTBALL = "FOOTBALL"
    BIBLE = "BIBLE"

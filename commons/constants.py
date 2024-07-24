from notifications.push import OneSignal
from notifications.sms import HostPinnacleSMS

SMS_PROVIDERS = [HostPinnacleSMS]
PUSH_PROVIDERS = [OneSignal]

SESSION_RESULT_DECIMAL_PLACES: int = 7

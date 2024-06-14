from hashlib import md5

from notifications.constants import SMS_PROVIDERS


def md5_hash(value: str) -> str:
    """Convert string value into hash"""
    return md5(value.encode()).hexdigest()


def send_sms(phone_number: str, message: str) -> None:
    for provider in SMS_PROVIDERS:
        if provider.send_sms(phone_number, message):
            return

    # Raise error if all providers failed here

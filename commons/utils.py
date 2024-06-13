from notifications.constants import SMS_PROVIDERS


def send_sms(phone_number: str, message: str) -> None:
    for provider in SMS_PROVIDERS:
        if provider.send_sms(phone_number, message):
            return

    # Raise error if all providers failed here

from celery import shared_task

from notifications.constants import SMS_PROVIDERS


@shared_task  # type: ignore
def send_sms(phone_number: str, message: str) -> bool:
    for provider in SMS_PROVIDERS:
        if provider.send_sms(phone_number, message):
            return True

    # Raise error if all providers failed here
    return False

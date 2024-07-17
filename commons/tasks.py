from celery import shared_task

from commons.constants import PUSH_PROVIDERS, SMS_PROVIDERS
from commons.raw_logger import logger


@shared_task  # type: ignore
def send_sms(*, phone_number: str, type: str, message: str) -> bool:
    logger.info("Sending sms in background...")
    for provider in SMS_PROVIDERS:
        if provider.send_sms(phone_number, type, message):
            return True

    # Raise error if all providers failed here
    logger.error("Failed to send sms in the background")
    return False


@shared_task  # type: ignore
def send_push(*, type: str, title: str, message: str, user_id: str) -> bool:
    logger.info("Sending push notification in background...")
    for provider in PUSH_PROVIDERS:
        if provider.send_push(type=type, title=title, message=message, user_id=user_id):
            return True

    # Raise error if all providers failed here
    logger.error("Failed to send push notification in the background")
    return False

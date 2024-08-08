from celery import shared_task

from commons.constants import SessionCategories
from commons.raw_logger import logger
from quiz.user_pairing import PairingService


@shared_task(name="pairing_service")  # type: ignore
def pairing_service() -> None:
    logger.info("Starting pairing service in background...")
    for category in SessionCategories:
        PairingService.execute_pairing(category=category.value)

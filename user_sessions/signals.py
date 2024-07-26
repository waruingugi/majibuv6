from uuid import uuid4

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.constants import (
    SESSION_WITHDRAWAL_DESCRIPTION,
    TransactionCashFlow,
    TransactionServices,
    TransactionStatuses,
    TransactionTypes,
)
from accounts.serializers.transactions import TransactionCreateSerializer
from commons.raw_logger import logger
from quiz.models import Result


@receiver(post_save, sender=Result)
def create_session_withdrawal_transaction_instance(
    sender, instance, created, **kwargs
) -> None:
    if created:
        logger.info(
            f"Creating withdrawal transaction instance for session played by {instance.user.phone_number}"
        )
        transaction_serializer = TransactionCreateSerializer(
            data={
                "external_transaction_id": str(uuid4()),
                "cash_flow": TransactionCashFlow.OUTWARD.value,
                "type": TransactionTypes.WITHDRAWAL.value,
                "status": TransactionStatuses.SUCCESSFUL.value,
                "service": TransactionServices.MAJIBU.value,
                "amount": settings.SESSION_STAKE,
                "description": SESSION_WITHDRAWAL_DESCRIPTION.format(
                    instance.user.phone_number, instance.session.category
                ),
            }
        )
        transaction_serializer.initial_data["user"] = instance.user.id

        if transaction_serializer.is_valid():
            transaction_obj = transaction_serializer.save()
            logger.info(
                f"External transaction id {transaction_obj.id} for session played saved successfully."
            )

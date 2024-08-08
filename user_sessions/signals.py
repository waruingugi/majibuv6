import math
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
from commons.constants import DuoSessionStatuses
from commons.raw_logger import logger
from commons.tasks import send_push
from notifications.constants import NotificationTypes, PushNotifications
from quiz.models import Result
from user_sessions.constants import (
    PARTIALLY_REFUND_SESSION_DESCRIPTION,
    REFUND_SESSION_DESCRIPTION,
    SESSION_LOSS_MESSAGE,
    SESSION_PARTIAL_REFUND_MESSAGE,
    SESSION_REFUND_MESSAGE,
    SESSION_WIN_DESCRIPION,
    SESSION_WIN_MESSAGE,
)
from user_sessions.models import DuoSession


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
                f"External transaction id {transaction_obj.id} for session played created successfully."
            )


@receiver(post_save, sender=DuoSession)
def create_duo_session_transaction_instance(
    sender, instance, created, **kwargs
) -> None:
    if created:
        """Update party_a's wallet to reflect the partial refund"""
        if instance.status == DuoSessionStatuses.PARTIALLY_REFUNDED.value:
            logger.info(
                f"Partially refund {instance.party_a.phone_number} for session {instance.session.category}."
            )
            description = PARTIALLY_REFUND_SESSION_DESCRIPTION.format(
                instance.party_a.phone_number, instance.session.category
            )
            partial_refund_amount = settings.SESSION_PARTIAL_REFUND_RATIO * float(
                instance.amount
            )
            partial_refund_amount = math.floor(
                partial_refund_amount
            )  # Round down to the nearest digit

            transaction_serializer = TransactionCreateSerializer(
                data={
                    "external_transaction_id": str(uuid4()),
                    "cash_flow": TransactionCashFlow.INWARD.value,
                    "type": TransactionTypes.REFUND.value,
                    "status": TransactionStatuses.SUCCESSFUL.value,
                    "service": TransactionServices.MAJIBU.value,
                    "amount": partial_refund_amount,
                    "description": description,
                }
            )
            transaction_serializer.initial_data["user"] = instance.party_a.id

            if transaction_serializer.is_valid():
                transaction_obj = transaction_serializer.save()
                logger.info(
                    f"External transaction id {transaction_obj.id} for refunded session created successfully."
                )

                push_message = SESSION_PARTIAL_REFUND_MESSAGE.format(
                    partial_refund_amount, instance.session.category
                )
                send_push.delay(
                    type=NotificationTypes.SESSION.value,
                    title=PushNotifications.SESSION_RESULTS.title,
                    message=push_message,
                    user_id=instance.party_a.id,
                )

        """Update party_a's wallet to reflect full refund"""
        if instance.status == DuoSessionStatuses.REFUNDED.value:
            logger.info(
                f"Refund {instance.party_a.phone_number} for session {instance.session.category}."
            )

            description = REFUND_SESSION_DESCRIPTION.format(
                instance.party_a.phone_number, instance.session.category
            )
            refund_amount = settings.SESSION_REFUND_RATIO * float(instance.amount)
            refund_amount = math.floor(refund_amount)  # Round down to the nearest digit

            transaction_serializer = TransactionCreateSerializer(
                data={
                    "external_transaction_id": str(uuid4()),
                    "cash_flow": TransactionCashFlow.INWARD.value,
                    "type": TransactionTypes.REFUND.value,
                    "status": TransactionStatuses.SUCCESSFUL.value,
                    "service": TransactionServices.MAJIBU.value,
                    "amount": refund_amount,
                    "description": description,
                }
            )
            transaction_serializer.initial_data["user"] = instance.party_a.id

            if transaction_serializer.is_valid():
                transaction_obj = transaction_serializer.save()
                logger.info(
                    f"External transaction id {transaction_obj.id} for refunded session created successfully."
                )

                push_message = SESSION_REFUND_MESSAGE.format(
                    refund_amount, instance.session.category
                )
                send_push.delay(
                    type=NotificationTypes.SESSION.value,
                    title=PushNotifications.SESSION_RESULTS.title,
                    message=push_message,
                    user_id=instance.party_a.id,
                )

        """Updates the winner's wallet to reflect the new amount"""
        if instance.status == DuoSessionStatuses.PAIRED.value:
            logger.info(
                f"Fund {instance.winner.phone_number} for session {instance.session.category}."
            )

            description = SESSION_WIN_DESCRIPION.format(
                instance.party_a.phone_number, instance.session.category
            )
            amount_won = settings.SESSION_WIN_RATIO * float(instance.amount)
            amount_won = math.floor(amount_won)  # Round down to the nearest digit

            transaction_serializer = TransactionCreateSerializer(
                data={
                    "external_transaction_id": str(uuid4()),
                    "cash_flow": TransactionCashFlow.INWARD.value,
                    "type": TransactionTypes.REWARD.value,
                    "status": TransactionStatuses.SUCCESSFUL.value,
                    "service": TransactionServices.MAJIBU.value,
                    "amount": amount_won,
                    "description": description,
                }
            )
            transaction_serializer.initial_data["user"] = instance.winner.id

            if transaction_serializer.is_valid():
                transaction_obj = transaction_serializer.save()
                logger.info(
                    f"External transaction id {transaction_obj.id} for session paired created successfully."
                )
                winner_message = SESSION_WIN_MESSAGE.format(
                    amount_won, instance.session.category
                )
                send_push.delay(
                    type=NotificationTypes.SESSION.value,
                    title=PushNotifications.SESSION_RESULTS.title,
                    message=winner_message,
                    user_id=instance.winner.id,
                )

                # Get the opponent id
                opponent = (
                    instance.party_a
                    if instance.winner != instance.party_a
                    else instance.party_b
                )
                opponent_message = SESSION_LOSS_MESSAGE.format(instance.category)

                push_message = SESSION_LOSS_MESSAGE.format(instance.session.category)
                send_push.delay(
                    type=NotificationTypes.SESSION.value,
                    title=PushNotifications.SESSION_RESULTS.title,
                    message=opponent_message,
                    user_id=opponent.id,
                )

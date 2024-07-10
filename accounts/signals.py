import json

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.constants import (
    TransactionCashFlow,
    TransactionServices,
    TransactionStatuses,
    TransactionTypes,
)
from accounts.models import MpesaPayment
from accounts.serializers.transactions import TransactionCreateSerializer
from commons.raw_logger import logger
from commons.serializers import UserPhoneNumberField

User = get_user_model()


@receiver(post_save, sender=MpesaPayment)
def post_update_create_transaction(sender, instance, created, **kwargs) -> None:
    """Create a deposit transaction instance"""
    if not created:
        # This block will only run if the instance was updated
        phone_field = UserPhoneNumberField()
        phone_number = phone_field.to_internal_value(instance.phone_number)
        user = User.objects.filter(phone_number=phone_number).first()

        if user:
            """Only record payments by registered users."""
            logger.info(f"Creating Ksh{instance.amount} deposit for {phone_number}.")
            transaction_serializer = TransactionCreateSerializer(
                data={
                    "external_transaction_id": instance.receipt_number,
                    "cash_flow": TransactionCashFlow.INWARD.value,
                    "type": TransactionTypes.DEPOSIT.value,
                    "status": TransactionStatuses.SUCCESSFUL.value,
                    "service": TransactionServices.MPESA.value,
                    "amount": float(instance.amount),
                    "external_response": json.dumps(instance.external_response),
                }
            )

            transaction_serializer.initial_data["user"] = user.id
            transaction_serializer.is_valid()
            transaction_serializer.save()

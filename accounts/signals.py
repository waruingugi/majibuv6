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
from accounts.models import Withdrawal
from accounts.serializers.transactions import TransactionCreateSerializer
from commons.raw_logger import logger
from commons.utils import calculate_b2c_withdrawal_charge

User = get_user_model()


@receiver(post_save, sender=Withdrawal)
def create_withdrawal_transaction_instance(sender, instance, created, **kwargs):
    if not created:  # Executes on model update ONLY
        user = User.objects.filter(phone_number=instance.phone_number).first()

        # Assert user exists AND the ´result_code´ is 0.
        # Any other result_code value means the M-Pesa B2C transaction failed.
        # See documentation for more info: https://developer.safaricom.co.ke/APIs/BusinessToCustomer
        if user and instance.result_code == 0:
            logger.info(f"Creating transaction instance for {user.phone_number}")

            transaction_serializer = TransactionCreateSerializer(
                data={
                    "external_transaction_id": instance.transaction_id,
                    "cash_flow": TransactionCashFlow.OUTWARD.value,
                    "type": TransactionTypes.WITHDRAWAL.value,
                    "status": TransactionStatuses.SUCCESSFUL.value,
                    "service": TransactionServices.MPESA.value,
                    "amount": instance.transaction_amount,
                    "fee": calculate_b2c_withdrawal_charge(instance.transaction_amount),
                    "external_response": json.dumps(instance.external_response),
                }
            )

            transaction_serializer.initial_data["user"] = user.id
            if transaction_serializer.is_valid():
                transaction_serializer.save()
            logger.info(
                f"External transaction id {instance.transaction_id} saved successfully."
            )

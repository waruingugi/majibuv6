from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework import serializers

from accounts.constants import (
    DEPOSIT_AMOUNT_CHOICES,
    MAX_WITHDRAWAL_AMOUNT,
    MIN_WITHDRAWAL_AMOUNT,
)
from accounts.models import MpesaPayment, Transaction, Withdrawal
from commons.errors import ErrorCodes
from commons.raw_logger import logger
from commons.serializers import UserPhoneNumberField
from commons.utils import calculate_b2c_withdrawal_charge, md5_hash

User = get_user_model()


class WithdrawAmountSerializer(serializers.Serializer):
    amount = serializers.IntegerField(
        required=True, min_value=MIN_WITHDRAWAL_AMOUNT, max_value=MAX_WITHDRAWAL_AMOUNT
    )

    def validate(self, data):
        request = self.context.get("request")
        if not request:
            raise serializers.ValidationError(
                "Request context is required for validation."
            )

        logger.info(
            f"Processing {request.user.phone_number} withdrawal request fo Kshs: {data['amount']}"
        )
        user_balance = Transaction.objects.get_user_balance(user=request.user)
        withdrawal_amount = data["amount"]
        total_withdrawal_charge = withdrawal_amount + calculate_b2c_withdrawal_charge(
            withdrawal_amount
        )

        if user_balance < total_withdrawal_charge:
            raise serializers.ValidationError(
                ErrorCodes.INSUFFICIENT_BALANCE_TO_WITHDRAW.value.format(
                    withdrawal_amount
                )
            )

        if cache.get(md5_hash(f"{request.user.phone_number}:withdraw_request")):
            raise serializers.ValidationError(
                ErrorCodes.SIMILAR_WITHDRAWAL_REQUEST.value.format(withdrawal_amount)
            )

        return data


class DepositAmountSerializer(serializers.Serializer):
    amount = serializers.ChoiceField(required=True, choices=DEPOSIT_AMOUNT_CHOICES)


class MpesaPaymentCreateSerializer(serializers.ModelSerializer):
    phone_number = UserPhoneNumberField()

    class Meta:
        model = MpesaPayment
        fields = [
            "phone_number",
            "merchant_request_id",
            "checkout_request_id",
            "response_code",
            "response_description",
            "customer_message",
        ]


class WithdrawalCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Withdrawal
        fields = [
            "conversation_id",
            "originator_conversation_id",
            "response_code",
            "response_description",
            "transaction_amount",
            "phone_number",
        ]
        extra_kwargs = {"transaction_amount": {"required": False}}


# -----------------------------------------------------------------

# STKPush serializers


class CallbackMetadataSerializer(serializers.Serializer):
    Item = serializers.ListField(child=serializers.DictField())


class C2BSTKResultSerializer(serializers.Serializer):
    MerchantRequestID = serializers.CharField()
    CheckoutRequestID = serializers.CharField()
    ResultCode = serializers.IntegerField()
    ResultDesc = serializers.CharField()
    CallbackMetadata = CallbackMetadataSerializer(required=False)


class STKCallbackSerializer(serializers.Serializer):
    stkCallback = C2BSTKResultSerializer()


class STKPushSerializer(serializers.Serializer):
    Body = STKCallbackSerializer()


# End of STKPush serializers


# M-Pesa B2C serializers
class ReferenceDataSerializer(serializers.Serializer):
    ReferenceItem = serializers.DictField()


class ResultParametersSerializer(serializers.Serializer):
    ResultParameter = serializers.ListField(child=serializers.DictField())


class B2CResultSerializer(serializers.Serializer):
    ResultType = serializers.IntegerField()
    ResultCode = serializers.IntegerField()
    ResultDesc = serializers.CharField()
    OriginatorConversationID = serializers.CharField()
    ConversationID = serializers.CharField()
    TransactionID = serializers.CharField()
    ReferenceData = ReferenceDataSerializer()
    ResultParameters = ResultParametersSerializer(required=False)


class B2CResponseSerializer(serializers.Serializer):
    Result = B2CResultSerializer()


# End of M-Pesa B2C serializers

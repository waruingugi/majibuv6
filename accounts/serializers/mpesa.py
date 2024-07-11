from typing import List, Optional, Union

from django.contrib.auth import get_user_model
from django.core.cache import cache
from pydantic import BaseModel
from rest_framework import serializers

from accounts.constants import (
    DEPOSIT_AMOUNT_CHOICES,
    MAX_WITHDRAWAL_AMOUNT,
    MIN_WITHDRAWAL_AMOUNT,
)
from accounts.models import MpesaPayment, Transaction, Withdrawal
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
                f"You do not have sufficient balance to withdraw ksh {withdrawal_amount}"
            )

        if cache.get(md5_hash(f"{request.user.phone_number}:withdraw_request")):
            raise serializers.ValidationError(
                f"A similar withdrawal request for ksh {withdrawal_amount} is currently being processed."
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
        ]
        extra_kwargs = {"transaction_amount": {"required": False}}


class MpesaPaymentResultItemSerializer(BaseModel):
    Name: str
    Value: Optional[Union[int, str]] = ""


class MpesaPaymentResultCallbackMetadataSerializer(BaseModel):
    Item: List[MpesaPaymentResultItemSerializer]


class MpesaPaymentResultStkCallbackSerializer(BaseModel):
    MerchantRequestID: str
    CheckoutRequestID: str
    ResultCode: int
    ResultDesc: str
    CallbackMetadata: Optional[MpesaPaymentResultCallbackMetadataSerializer] = None


class MpesaDirectPaymentSerializer(BaseModel):
    TransactionType: str
    TransID: str
    TransTime: str
    TransAmount: str
    BusinessShortCode: str
    BillRefNumber: Optional[str] = ""
    InvoiceNumber: Optional[str] = ""
    OrgAccountBalance: Optional[str] = ""
    ThirdPartyTransID: Optional[str] = ""
    MSISDN: str
    FirstName: Optional[str] = ""
    MiddleName: Optional[str] = ""
    LastName: Optional[str] = ""


class KeyValueDict(BaseModel):
    Key: str
    Value: str | int | float


class WithdrawalReferenceItemSerializer(BaseModel):
    ReferenceItem: KeyValueDict


class WithdrawalResultBodyParameters(BaseModel):
    ResultParameter: List[KeyValueDict]


class WithdrawalResultBodySerializer(BaseModel):
    ResultType: int
    ResultCode: int
    ResultDesc: str
    OriginatorConversationID: str
    ConversationID: str
    TransactionID: str
    # ResultParameters: WithdrawalResultBodyParameters
    ReferenceData: WithdrawalReferenceItemSerializer


class WithdrawalResultSerializer(BaseModel):
    Result: WithdrawalResultBodySerializer


class MpesaPaymentResultBodySerializer(BaseModel):
    stkCallback: MpesaPaymentResultStkCallbackSerializer


class MpesaPaymentResultSerializer(BaseModel):
    Body: MpesaPaymentResultBodySerializer


# -----------------------------------------------------------------
class KeyValueSerializer(serializers.Serializer):
    Key = serializers.CharField()
    Value = serializers.CharField()


class ReferenceItemSerializer(KeyValueSerializer):
    pass


class ReferenceDataSerializer(serializers.Serializer):
    ReferenceItem = ReferenceItemSerializer()


class ResultParameterSerializer(KeyValueSerializer):
    pass


class ResultParametersSerializer(serializers.Serializer):
    ResultParameter = ResultParameterSerializer(many=True)


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

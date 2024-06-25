from typing import List, Optional, Union

from django.contrib.auth import get_user_model
from pydantic import BaseModel
from rest_framework import serializers

from accounts.constants import DEPOSIT_AMOUNT_CHOICES
from accounts.models import MpesaPayment, Transaction, Withdrawal
from commons.serializers import UserPhoneNumberField

User = get_user_model()


class DepositAmountSerializer(serializers.Serializer):
    amount = serializers.ChoiceField(required=True, choices=DEPOSIT_AMOUNT_CHOICES)


class TransactionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        exclude = ["description", "external_response"]
        extra_kwargs = {
            "id": {"read_only": True},
            "created_at": {"read_only": True},
            "updated_at": {"read_only": True},
            "initial_balance": {"read_only": True},
            "final_balance": {"read_only": True},
            "fee": {"required": False},
            "tax": {"required": False},
            "charge": {"required": False},
            "external_response": {"required": False},
        }


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
        ]


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
    Value: str


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
    ResultParameters: WithdrawalResultBodyParameters
    ReferenceData: WithdrawalReferenceItemSerializer


class WithdrawalResultSerializer(BaseModel):
    Result: WithdrawalResultBodySerializer


class MpesaPaymentResultBodySerializer(BaseModel):
    stkCallback: MpesaPaymentResultStkCallbackSerializer


class MpesaPaymentResultSerializer(BaseModel):
    Body: MpesaPaymentResultBodySerializer

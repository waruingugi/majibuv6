from django.contrib.auth import get_user_model
from rest_framework import serializers

from accounts.models import MpesaPayment, Transaction, Withdrawal
from commons.serializers import UserPhoneNumberField

User = get_user_model()


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

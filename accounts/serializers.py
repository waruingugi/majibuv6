from django.contrib.auth import get_user_model
from rest_framework import serializers

from accounts.models import Transaction

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

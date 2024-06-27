from rest_framework import serializers

from accounts.models import Transaction
from users.serializers import UserReadSerializer


class TransactionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        exclude = ["charge"]
        extra_kwargs = {
            "id": {"read_only": True},
            "created_at": {"read_only": True},
            "updated_at": {"read_only": True},
            "initial_balance": {"read_only": True},
            "final_balance": {"read_only": True},
            "fee": {"required": False},
            "tax": {"required": False},
            "description": {"required": False},
            "external_response": {"required": False},
        }


class TransactionRetrieveUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at", "user")


class TransactionListSerializer(serializers.ModelSerializer):
    user = UserReadSerializer()

    class Meta:
        model = Transaction
        exclude = ["id", "created_at", "updated_at", "description", "external_response"]

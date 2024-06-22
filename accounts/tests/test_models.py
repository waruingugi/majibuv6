import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.serializers import TransactionCreateSerializer

User = get_user_model()


class TransactionTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone_number="+254701301401",
            password="password123",
            username="testuser",
        )
        self.sample_positive_transaction_instance_info = {
            "external_transaction_id": "SKJO89BVH",
            "cash_flow": "INWARD",
            "type": "DEPOSIT",
            "status": "SUCCESSFUL",
            "service": "MPESA",
            "description": "",
            "amount": 1.0,
            "external_response": json.dumps({}),
        }

    def test_create_positive_transaction_instance_successfully(self):
        serializer = TransactionCreateSerializer(
            data=self.sample_positive_transaction_instance_info
        )
        serializer.initial_data["user"] = self.user.id

        self.assertTrue(serializer.is_valid())
        transaction = serializer.save(user=self.user)

        self.assertEqual(transaction.charge, Decimal(0.00))
        # self.assertEqual(transaction.initial_balance, Decimal(0.00))
        # self.assertEqual(transaction.final_balance, Decimal(1.00))

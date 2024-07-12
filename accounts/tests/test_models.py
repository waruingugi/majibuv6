import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.constants import STKPUSH_DEPOSIT_DESCRPTION
from accounts.models import MpesaPayment, Transaction
from accounts.serializers.mpesa import (
    MpesaPaymentCreateSerializer,
    WithdrawalCreateSerializer,
)
from accounts.serializers.transactions import TransactionCreateSerializer
from accounts.tests.test_data import (
    mock_stk_push_response,
    mock_stk_push_result,
    withdrawal_obj_instance,
)
from accounts.utils import process_mpesa_stk
from commons.tests.base_tests import BaseUserAPITestCase

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
            "description": STKPUSH_DEPOSIT_DESCRPTION.format(
                1.0, self.user.phone_number
            ),
            "amount": 1.0,
            "external_response": json.dumps({}),
        }

    def test_model_returns_user_balance(self) -> None:
        serializer = TransactionCreateSerializer(
            data=self.sample_positive_transaction_instance_info
        )
        serializer.initial_data["user"] = self.user.id
        serializer.is_valid()
        serializer.save()

        self.assertEqual(
            self.sample_positive_transaction_instance_info["amount"],
            float(Transaction.objects.get_user_balance(self.user)),
        )

    def test_create_positive_transaction_instance_successfully(self):
        serializer = TransactionCreateSerializer(
            data=self.sample_positive_transaction_instance_info
        )
        serializer.initial_data["user"] = self.user.id

        self.assertTrue(serializer.is_valid())
        transaction = serializer.save(user=self.user)

        self.assertEqual(transaction.charge, Decimal(1.00))
        self.assertEqual(transaction.initial_balance, Decimal(0.00))
        self.assertEqual(transaction.final_balance, Decimal(1.00))

    def test_create_negative_transaction_instance_successfully(self):
        data = self.sample_positive_transaction_instance_info.copy()
        data["amount"] = 100
        serializer = TransactionCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        transaction = serializer.save(user=self.user)

        data = {
            "external_transaction_id": "ext124",
            "cash_flow": "OUTWARD",
            "type": "WITHDRAWAL",
            "amount": 36.0,
            "fee": 16.0,
            "tax": 0.0,
            "status": "PENDING",
            "service": "Test Service",
            "description": "Test description",
            "external_response": {},
        }
        serializer = TransactionCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        transaction = serializer.save(user=self.user)

        self.assertEqual(transaction.charge, 52.00)
        self.assertEqual(transaction.initial_balance, 100.00)
        self.assertEqual(transaction.final_balance, 48.00)


class MpesaPaymentTestCase(BaseUserAPITestCase):
    def setUp(self) -> None:
        self.user = self.create_user()
        self.mock_stk_push_response = mock_stk_push_response
        self.mock_stk_push_result = mock_stk_push_result

        self.serializer = MpesaPaymentCreateSerializer(
            data={
                "phone_number": str(self.user.phone_number),
                "merchant_request_id": self.mock_stk_push_response["MerchantRequestID"],
                "checkout_request_id": self.mock_stk_push_response["CheckoutRequestID"],
                "response_code": self.mock_stk_push_response["ResponseCode"],
                "response_description": self.mock_stk_push_response[
                    "ResponseDescription"
                ],
                "customer_message": self.mock_stk_push_response["CustomerMessage"],
            }
        )

    def test_mpesa_payment_is_created_successfully(self) -> None:
        self.assertTrue(self.serializer.is_valid())
        mpesa_payment = self.serializer.save()

        self.assertIsNotNone(mpesa_payment)
        self.assertIsNone(mpesa_payment.amount)
        self.assertIsNone(mpesa_payment.receipt_number)
        self.assertEqual(mpesa_payment.phone_number, str(self.user.phone_number))

    def test_mpesa_payment_is_updated_successfully(self):
        self.assertTrue(self.serializer.is_valid())
        mpesa_payment = self.serializer.save()

        process_mpesa_stk(self.mock_stk_push_result["Body"]["stkCallback"])
        mpesa_payment = MpesaPayment.objects.get(id=mpesa_payment.id)

        self.assertIsNotNone(mpesa_payment.receipt_number)
        self.assertEqual(mpesa_payment.amount, Decimal(1.00))


class WithdrawalTestCase(TestCase):
    def test_create_withdrawal_instance_successfully(self):
        serializer = WithdrawalCreateSerializer(data=withdrawal_obj_instance)
        self.assertTrue(serializer.is_valid())
        withdrawal = serializer.save()

        self.assertEqual(
            withdrawal.conversation_id, withdrawal_obj_instance["conversation_id"]
        )
        self.assertEqual(
            withdrawal.originator_conversation_id,
            withdrawal_obj_instance["originator_conversation_id"],
        )

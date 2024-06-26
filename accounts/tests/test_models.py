import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.constants import STKPUSH_DEPOSIT_DESCRPTION
from accounts.models import MpesaPayment, Transaction
from accounts.serializers.mpesa import (
    MpesaPaymentCreateSerializer,
    MpesaPaymentResultCallbackMetadataSerializer,
    MpesaPaymentResultStkCallbackSerializer,
    WithdrawalCreateSerializer,
)
from accounts.serializers.transactions import TransactionCreateSerializer
from accounts.utils import process_mpesa_stk

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


class MpesaPaymentTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone_number="+254701301401",
            password="password123",
            username="testuser",
        )
        self.mock_stk_push_response = {
            "phone_number": "254701301401",
            "merchant_request_id": "29115-34620561-1",
            "checkout_request_id": "ws_CO_191220191020363925",
            "response_code": "0",
            "response_description": "Success. Request accepted for processing",
            "customer_message": "Success. Request accepted for processing",
        }

        mock_stk_push_result = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "29115-34620561-1",
                    "CheckoutRequestID": "ws_CO_191220191020363925",
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": 1.00},
                            {"Name": "MpesaReceiptNumber", "Value": "NLJ7RT61SV"},
                            {"Name": "TransactionDate", "Value": 20191219102115},
                            {"Name": "PhoneNumber", "Value": 254708374149},
                        ]
                    },
                }
            }
        }

        serialized_call_back_metadata = MpesaPaymentResultCallbackMetadataSerializer(
            **mock_stk_push_result["Body"]["stkCallback"]["CallbackMetadata"]  # type: ignore
        )

        self.serialized_call_back = MpesaPaymentResultStkCallbackSerializer(
            CallbackMetadata=serialized_call_back_metadata,
            MerchantRequestID=mock_stk_push_result["Body"]["stkCallback"][
                "MerchantRequestID"
            ],
            CheckoutRequestID=mock_stk_push_result["Body"]["stkCallback"][
                "CheckoutRequestID"
            ],
            ResultCode=mock_stk_push_result["Body"]["stkCallback"]["ResultCode"],
            ResultDesc=mock_stk_push_result["Body"]["stkCallback"]["ResultDesc"],
        )

    def test_mpesa_payment_is_created_successfully(self):
        serializer = MpesaPaymentCreateSerializer(data=self.mock_stk_push_response)
        self.assertTrue(serializer.is_valid())
        mpesa_payment = serializer.save()

        self.assertIsNotNone(mpesa_payment)
        self.assertIsNone(mpesa_payment.amount)
        self.assertIsNone(mpesa_payment.receipt_number)
        self.assertEqual(mpesa_payment.phone_number, str(self.user.phone_number))

    def test_mpesa_payment_is_updated_successfully(self):
        serializer = MpesaPaymentCreateSerializer(data=self.mock_stk_push_response)
        self.assertTrue(serializer.is_valid())
        mpesa_payment = serializer.save()

        process_mpesa_stk(self.serialized_call_back)

        mpesa_payment = MpesaPayment.objects.get(id=mpesa_payment.id)

        self.assertIsNotNone(mpesa_payment.receipt_number)
        self.assertEqual(mpesa_payment.amount, Decimal(1.00))


class WithdrawalTestCase(TestCase):
    def setUp(self):
        self.sample_b2c_response = {
            "conversation_id": "AG_20191219_00005797af5d7d75f652",
            "originator_conversation_id": "16740-34861180-1",
            "response_code": "0",
            "response_description": "Accept the service request successfully.",
        }

    def test_create_withdrawal_instance_successfully(self):
        serializer = WithdrawalCreateSerializer(data=self.sample_b2c_response)
        self.assertTrue(serializer.is_valid())
        withdrawal = serializer.save()

        self.assertEqual(
            withdrawal.conversation_id, self.sample_b2c_response["conversation_id"]
        )
        self.assertEqual(
            withdrawal.originator_conversation_id,
            self.sample_b2c_response["originator_conversation_id"],
        )

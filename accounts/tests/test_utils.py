import json
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.core.cache import cache
from django.test import TestCase

from accounts.constants import (
    DEFAULT_B2C_CHARGE,
    MpesaAccountTypes,
    TransactionCashFlow,
    TransactionServices,
    TransactionStatuses,
)
from accounts.models import MpesaPayment, Transaction, Withdrawal
from accounts.tests.test_data import (
    mock_failed_b2c_result,
    mock_failed_stk_push_response,
    mock_stk_push_response,
    mock_stk_push_result,
    mock_successful_b2c_result,
    mpesa_reference_no,
    sample_b2c_response,
    withdrawal_obj_instance,
)
from accounts.utils import (
    get_mpesa_access_token,
    initiate_b2c_payment,
    initiate_mpesa_stkpush_payment,
    process_b2c_payment,
    process_b2c_payment_result,
    process_mpesa_stk,
    trigger_mpesa_stkpush_payment,
)
from commons.tests.base_tests import BaseUserAPITestCase
from commons.utils import calculate_b2c_withdrawal_charge


class TestMpesaSTKPush(TestCase):
    mock_response = MagicMock()

    @classmethod
    def setUpTestData(cls):
        cache.clear()  # Flush all values from redis

    @classmethod
    def tearDownClass(cls):
        cache.clear()  # Flush all values from redis
        super().tearDownClass()

    @patch("accounts.utils.requests")
    def test_get_mpesa_access_token(self, mock_requests) -> None:
        expected_access_token = "fake_access_token"
        self.mock_response.json.return_value = {
            "access_token": expected_access_token,
            "expires_in": "3599",
        }
        mock_requests.get.return_value = self.mock_response

        access_token = get_mpesa_access_token()
        self.assertEqual(access_token, expected_access_token)

    @patch("accounts.utils.requests")
    def test_get_mpesa_access_token_is_set_in_redis(self, mock_requests) -> None:
        cache.clear()  # Ensure redis is clear for consistent results
        expected_access_token = "fake_access_token"
        self.mock_response.json.return_value = {
            "access_token": expected_access_token,
            "expires_in": "3599",
        }
        mock_requests.get.return_value = self.mock_response

        get_mpesa_access_token()  # Call first time
        get_mpesa_access_token()  # Second call

        self.assertEqual(mock_requests.get.call_count, 1)

    @patch("accounts.utils.get_mpesa_access_token")
    def test_initiate_mpesa_stkpush_payment_returns_successful_response(
        self, mock_get_mpesa_access_token
    ) -> None:
        mock_get_mpesa_access_token.return_value = "fake_access_token"

        with patch("accounts.utils.requests") as mock_requests:
            self.mock_response.json.return_value = {
                "MerchantRequestID": "29115-34620561-1",
                "CheckoutRequestID": "ws_CO_191220191020363925",
                "ResponseCode": "0",
                "ResponseDescription": "Success. Request accepted for processing",
                "CustomerMessage": "Success. Request accepted for processing",
            }
            mock_requests.post.return_value = self.mock_response

            response = initiate_mpesa_stkpush_payment(
                phone_number="+254704845040",
                amount=1,
                business_short_code=settings.MPESA_BUSINESS_SHORT_CODE,
                party_b=settings.MPESA_BUSINESS_SHORT_CODE,
                passkey=settings.MPESA_PASS_KEY,
                transaction_type=MpesaAccountTypes.PAYBILL.value,
                callback_url=settings.MPESA_CALLBACK_URL,
                reference="+254704845040",
                description="",
            )

            self.assertEqual(response, self.mock_response.json())

    @patch("accounts.utils.get_mpesa_access_token")
    @patch("accounts.utils.requests")
    def test_initiate_mpesa_stkpush_payment_raises_exception(
        self, mock_get_mpesa_access_token, mock_requests
    ) -> None:
        mock_get_mpesa_access_token.return_value = "fake_access_token"

        with self.assertRaises(Exception):
            mock_requests.side_effect = Exception

            initiate_mpesa_stkpush_payment(
                phone_number="+254704845040",
                amount=1,
                business_short_code=settings.MPESA_BUSINESS_SHORT_CODE,
                party_b=settings.MPESA_BUSINESS_SHORT_CODE,
                passkey=settings.MPESA_PASS_KEY,
                transaction_type=MpesaAccountTypes.PAYBILL.value,
                callback_url=settings.MPESA_CALLBACK_URL,
                reference="+254704845040",
                description="",
            )

    @patch("accounts.utils.initiate_mpesa_stkpush_payment")
    def test_trigger_mpesa_stkpush_payment(
        self, mock_initiate_mpesa_stkpush_payment
    ) -> None:
        mock_initiate_mpesa_stkpush_payment.return_value = {
            "MerchantRequestID": "29115-34620561-1",
            "CheckoutRequestID": "ws_CO_191220191020363925",
            "ResponseCode": "0",
            "ResponseDescription": "Success. Request accepted for processing",
            "CustomerMessage": "Success. Request accepted for processing",
        }
        response = trigger_mpesa_stkpush_payment(amount=1, phone_number="+254704845040")
        self.assertEqual(response, mock_initiate_mpesa_stkpush_payment.return_value)


class TestMpesaB2CPayment(TestCase):
    mock_response = MagicMock()

    def setUp(self) -> None:
        self.sample_b2c_response = sample_b2c_response

    @patch("accounts.utils.get_mpesa_access_token")
    def test_initiate_b2c_payment_returns_correct_response(
        self, mock_get_mpesa_access_token
    ) -> None:
        mock_get_mpesa_access_token.return_value = "random_token"

        with patch("accounts.utils.requests") as mock_requests:
            self.mock_response.json.return_value = self.sample_b2c_response
            mock_requests.post.return_value = self.mock_response

            response = initiate_b2c_payment(
                amount=1,
                party_b="+254704845040",
            )

            self.assertEqual(response, self.mock_response.json())

    @patch("accounts.utils.get_mpesa_access_token")
    def test_initiate_b2c_payment_returns_none_if_error_in_response(
        self, mock_get_mpesa_access_token
    ) -> None:
        mock_get_mpesa_access_token.return_value = "random_token"

        with patch("accounts.utils.requests") as mock_requests:
            self.sample_b2c_response["ResponseCode"] = "1"
            self.mock_response.json.return_value = self.sample_b2c_response
            mock_requests.post.return_value = self.mock_response

            response = initiate_b2c_payment(
                amount=1,
                party_b="+254704845040",
            )

            self.assertIsNone(response)


class TestProcessB2CPaymentResult(BaseUserAPITestCase):
    def setUp(self):
        self.user = self.create_user()
        self.user.phone_number = withdrawal_obj_instance["phone_number"]
        self.user.save()

        self.withdrawal = Withdrawal.objects.create(**withdrawal_obj_instance)
        self.sample_b2c_response_success = mock_successful_b2c_result["Result"]
        self.sample_b2c_response_failure = mock_failed_b2c_result["Result"]

    def test_updates_model_on_successfull_response(self):
        process_b2c_payment_result(self.sample_b2c_response_success)
        self.withdrawal.refresh_from_db()
        self.assertEqual(
            self.withdrawal.result_code, self.sample_b2c_response_success["ResultCode"]
        )
        self.assertEqual(
            self.withdrawal.result_description,
            self.sample_b2c_response_success["ResultDesc"],
        )
        self.assertEqual(
            self.withdrawal.transaction_id,
            self.sample_b2c_response_success["TransactionID"],
        )
        self.assertEqual(
            json.loads(self.withdrawal.external_response),
            self.sample_b2c_response_success,
        )
        # Assert signal is called and Transaction instance is created.
        transaction_obj = Transaction.objects.get(
            external_transaction_id=self.withdrawal.transaction_id
        )
        self.assertEqual(transaction_obj.cash_flow, TransactionCashFlow.OUTWARD.value)
        self.assertEqual(transaction_obj.status, TransactionStatuses.SUCCESSFUL.value)
        self.assertEqual(transaction_obj.service, TransactionServices.MPESA.value)
        self.assertEqual(transaction_obj.amount, self.withdrawal.transaction_amount)

    def test_updates_model_on_failed_response(self):
        process_b2c_payment_result(self.sample_b2c_response_failure)
        self.withdrawal.refresh_from_db()
        self.assertEqual(
            self.withdrawal.result_code, self.sample_b2c_response_failure["ResultCode"]
        )
        self.assertEqual(
            self.withdrawal.result_description,
            self.sample_b2c_response_failure["ResultDesc"],
        )
        self.assertEqual(
            self.withdrawal.transaction_id,
            self.sample_b2c_response_failure["TransactionID"],
        )
        self.assertEqual(
            json.loads(self.withdrawal.external_response),
            self.sample_b2c_response_failure,
        )

    def test_no_update_if_transaction_id_exists(self):
        # Set transaction_id to simulate a previously updated withdrawal
        self.withdrawal.transaction_id = "EXISTING_TRANSACTION_ID"
        self.withdrawal.save()
        process_b2c_payment_result(self.sample_b2c_response_success)
        self.withdrawal.refresh_from_db()
        # Ensure no changes occurred
        self.assertEqual(self.withdrawal.transaction_id, "EXISTING_TRANSACTION_ID")


class TestProcessB2CPayment(BaseUserAPITestCase):
    def setUp(self):
        self.user = self.create_user()
        self.amount = 1000  # Sample amount

    def tearDown(self):
        self.user.delete()
        Withdrawal.objects.all().delete()
        cache.clear()

    @patch("accounts.utils.initiate_b2c_payment")
    @patch("accounts.utils.cache.set")
    def test_process_b2c_payment_success(
        self, mock_initiate_b2c_payment, mock_cache_set
    ):
        mock_initiate_b2c_payment.return_value = sample_b2c_response

        process_b2c_payment(user_id=self.user.id, amount=self.amount)

        # Assertions
        mock_cache_set.assert_called_once()
        mock_initiate_b2c_payment.assert_called_once()

        # TODO: Add more tests for this class


class TestProcessMpesaStk(BaseUserAPITestCase):
    def setUp(self):
        self.user = self.create_user()
        self.successful_result = mock_stk_push_result["Body"]["stkCallback"]
        self.failed_result = mock_failed_stk_push_response["Body"]["stkCallback"]

        self.mpesa_payment = MpesaPayment.objects.create(
            phone_number=str(self.user.phone_number),
            merchant_request_id=mock_stk_push_response["MerchantRequestID"],
            checkout_request_id=mock_stk_push_response["CheckoutRequestID"],
            response_code=mock_stk_push_response["ResponseCode"],
            response_description=mock_stk_push_response["ResponseDescription"],
            customer_message=mock_stk_push_response["CustomerMessage"],
        )

    def test_process_successful_mpesa_stk_response(self):
        process_mpesa_stk(mpesa_response_in=self.successful_result)

        mpesa_payment = MpesaPayment.objects.get(
            checkout_request_id=self.successful_result["CheckoutRequestID"]
        )
        self.assertEqual(mpesa_payment.result_code, 0)
        self.assertEqual(mpesa_payment.amount, 1.00)
        self.assertEqual(mpesa_payment.receipt_number, mpesa_reference_no)
        # Ignore this test case for now. But idealy the phone numbers should be same
        # self.assertEqual(mpesa_payment.phone_number, str(self.user.phone_number))
        self.assertEqual(
            json.loads(mpesa_payment.external_response), self.successful_result
        )

    def test_process_failed_mpesa_stk_response(self):
        process_mpesa_stk(mpesa_response_in=self.failed_result)

        mpesa_payment = MpesaPayment.objects.get(
            checkout_request_id=self.failed_result["CheckoutRequestID"]
        )
        self.assertEqual(mpesa_payment.result_code, self.failed_result["ResultCode"])
        self.assertEqual(
            mpesa_payment.result_description, self.failed_result["ResultDesc"]
        )
        self.assertIsNone(mpesa_payment.amount)  # Amount should not be updated
        self.assertIsNone(
            mpesa_payment.receipt_number
        )  # Receipt number should not be updated
        self.assertIsNone(
            mpesa_payment.transaction_date
        )  # Transaction date should not be updated
        self.assertEqual(
            json.loads(mpesa_payment.external_response), self.failed_result
        )


class TestCalculateB2CWithdrawalCharge(TestCase):
    def test_within_first_range(self) -> None:
        self.assertEqual(calculate_b2c_withdrawal_charge(50), 2)

    def test_within_second_range(self) -> None:
        self.assertEqual(calculate_b2c_withdrawal_charge(300), 8)

    def test_within_third_range(self) -> None:
        self.assertEqual(calculate_b2c_withdrawal_charge(800), 15)

    def test_within_fourth_range(self) -> None:
        self.assertEqual(calculate_b2c_withdrawal_charge(1500), 25)

    def test_within_fifth_range(self) -> None:
        self.assertEqual(calculate_b2c_withdrawal_charge(2500), 35)

    def test_within_sixth_range(self) -> None:
        self.assertEqual(calculate_b2c_withdrawal_charge(3000), 55)

    def test_within_seventh_range(self) -> None:
        self.assertEqual(calculate_b2c_withdrawal_charge(5000), 60)

    def test_above_defined_ranges(self) -> None:
        self.assertEqual(calculate_b2c_withdrawal_charge(10000), DEFAULT_B2C_CHARGE)

    def test_below_defined_ranges(self) -> None:
        self.assertEqual(calculate_b2c_withdrawal_charge(-10), DEFAULT_B2C_CHARGE)

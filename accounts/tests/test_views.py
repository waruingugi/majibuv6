from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from accounts.constants import DEPOSIT_AMOUNT_CHOICES, MPESA_WHITE_LISTED_IPS
from accounts.models import Transaction
from accounts.tests.test_data import (
    mock_paybill_deposit_response,
    mock_stk_push_result,
    mock_successful_b2c_result,
)
from commons.throttles import MpesaSTKPushThrottle, MpesaWithdrawalThrottle

User = get_user_model()


class WithdrawalRequestTimeoutViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("mpesa:withdrawal-timeout")

    def test_white_listed_ip_can_make_post_request(self) -> None:
        for ip in MPESA_WHITE_LISTED_IPS:
            self.client.defaults["REMOTE_ADDR"] = ip
            response = self.client.post(self.url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_white_listed_ip_cannot_make_post_request(self) -> None:
        non_white_listed_ip = "192.0.2.1"
        self.client.defaults["REMOTE_ADDR"] = non_white_listed_ip
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class WithdrawalResultViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse(
            "mpesa:withdrawal-result"
        )  # Replace with your actual URL name
        self.mock_successful_b2c_result = mock_successful_b2c_result

    @patch("accounts.views.mpesa.process_b2c_payment_result_task.delay")
    def test_white_listed_ip_can_make_post_request(self, mock_task) -> None:
        for ip in MPESA_WHITE_LISTED_IPS:
            self.client.defaults["REMOTE_ADDR"] = ip
            response = self.client.post(
                self.url, data=self.mock_successful_b2c_result, format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_white_listed_ip_cannot_make_post_request(self) -> None:
        non_white_listed_ip = "192.0.2.1"
        self.client.defaults["REMOTE_ADDR"] = non_white_listed_ip
        response = self.client.post(
            self.url, data=self.mock_successful_b2c_result, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("accounts.views.mpesa.process_b2c_payment_result_task.delay")
    def test_successful_request_triggers_background_task(self, mock_task) -> None:
        ip = MPESA_WHITE_LISTED_IPS[0]
        self.client.defaults["REMOTE_ADDR"] = ip
        response = self.client.post(
            self.url, data=self.mock_successful_b2c_result, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_task.assert_called_once()


class PaybillPaymentConfirmationViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("mpesa:paybill-confirmation")
        self.mock_paybill_deposit_response = mock_paybill_deposit_response

    @patch("accounts.views.mpesa.process_mpesa_paybill_payment_task.delay")
    def test_white_listed_ip_can_make_post_request(self, mock_task) -> None:
        for ip in MPESA_WHITE_LISTED_IPS:
            self.client.defaults["REMOTE_ADDR"] = ip
            response = self.client.post(
                self.url, data=self.mock_paybill_deposit_response, format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_white_listed_ip_cannot_make_post_request(self) -> None:
        non_white_listed_ip = "192.0.2.1"
        self.client.defaults["REMOTE_ADDR"] = non_white_listed_ip
        response = self.client.post(
            self.url, data=self.mock_paybill_deposit_response, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("accounts.views.mpesa.process_mpesa_paybill_payment_task.delay")
    def test_successful_request_triggers_background_task(self, mock_task) -> None:
        ip = MPESA_WHITE_LISTED_IPS[0]
        self.client.defaults["REMOTE_ADDR"] = ip
        response = self.client.post(
            self.url, data=self.mock_paybill_deposit_response, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_task.assert_called_once()


class STKPushCallbackViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("mpesa:stkpush-callback")
        self.mock_stk_push_result = mock_stk_push_result

    @patch("accounts.views.mpesa.process_mpesa_stk_task.delay")
    def test_white_listed_ip_can_make_post_request(self, mock_task) -> None:
        for ip in MPESA_WHITE_LISTED_IPS:
            self.client.defaults["REMOTE_ADDR"] = ip
            response = self.client.post(
                self.url, data=self.mock_stk_push_result, format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_white_listed_ip_cannot_post(self) -> None:
        non_white_listed_ip = "192.0.2.1"
        self.client.defaults["REMOTE_ADDR"] = non_white_listed_ip
        response = self.client.post(
            self.url, data=self.mock_stk_push_result, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("accounts.views.mpesa.process_mpesa_stk_task.delay")
    def test_successful_request_triggers_background_task(self, mock_task) -> None:
        ip = MPESA_WHITE_LISTED_IPS[0]
        self.client.defaults["REMOTE_ADDR"] = ip
        response = self.client.post(
            self.url, data=self.mock_stk_push_result, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_task.assert_called_once()


class TriggerSTKPushViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("mpesa:trigger-stkpush")  # Replace with your actual URL name
        self.user = User.objects.create_user(
            username="testuser", password="testpassword", phone_number="+254712345678"
        )
        self.client.force_authenticate(user=self.user)
        self.sample_deposit_data = {"amount": DEPOSIT_AMOUNT_CHOICES[0]}
        self.invalid_deposit_data = {
            "amount": 15000000
        }  # Not in DEPOSIT_AMOUNT_CHOICES

    @patch("accounts.views.mpesa.trigger_mpesa_stkpush_payment_task.delay")
    def test_successful_request_calls_background_task(self, mock_task):
        response = self.client.post(
            self.url, data=self.sample_deposit_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_task.assert_called_once()

    def test_view_successfully_throttles_requests(self):
        for _ in range(3):
            response = self.client.post(
                self.url, data=self.sample_deposit_data, format="json"
            )

        response = self.client.post(
            self.url, data=self.sample_deposit_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        MpesaSTKPushThrottle.cache.clear()  # Reset throttling

    def test_view_rejects_invalid_post_request(self):
        response = self.client.post(
            self.url, data=self.invalid_deposit_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("amount", response.data)


class WithdrawalRequestViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse(
            "mpesa:trigger-withdrawal"
        )  # Replace with your actual URL name
        self.user = User.objects.create_user(
            username="testuser", password="testpassword", phone_number="+254712345678"
        )
        self.client.force_authenticate(user=self.user)
        self.sample_withdrawal_data = {"amount": 100}
        self.insufficient_funds_data = {"amount": 900}
        self.similar_request_data = {"amount": 50}

    @patch("accounts.views.mpesa.process_b2c_payment_task.delay")
    def test_successful_request_calls_delay_task(self, mock_task):
        with patch.object(Transaction.objects, "get_user_balance", return_value=500):
            response = self.client.post(
                self.url, data=self.sample_withdrawal_data, format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            mock_task.assert_called_once()
            MpesaWithdrawalThrottle.cache.clear()

    @patch("accounts.views.mpesa.process_b2c_payment_task.delay")
    def test_view_successfully_throttles_requests(self, mock_task):
        with patch.object(Transaction.objects, "get_user_balance", return_value=500):
            for _ in range(5):
                self.client.post(
                    self.url, data=self.sample_withdrawal_data, format="json"
                )

            response = self.client.post(
                self.url, data=self.sample_withdrawal_data, format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
            MpesaWithdrawalThrottle.cache.clear()  # Reset throttling

    def test_view_fails_if_user_has_insufficient_funds(self):
        with patch.object(Transaction.objects, "get_user_balance", return_value=50):
            response = self.client.post(
                self.url, data=self.insufficient_funds_data, format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            MpesaWithdrawalThrottle.cache.clear()  # Reset throttling

    @patch("accounts.views.mpesa.process_b2c_payment_task.delay")
    def test_invalid_serializer(self, mock_task):
        invalid_data = {"amount": 9999}  # Not within min and max values
        response = self.client.post(self.url, data=invalid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("amount", response.data)
        mock_task.assert_not_called()
        MpesaWithdrawalThrottle.cache.clear()

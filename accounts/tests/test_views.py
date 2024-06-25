from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from accounts.constants import MPESA_WHITE_LISTED_IPS


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
        self.sample_successful_b2c_result = {
            "Result": {
                "ResultType": 0,
                "ResultCode": 0,
                "ResultDesc": "The service request is processed successfully.",
                "OriginatorConversationID": "16740-34861180-1",
                "ConversationID": "AG_20191219_00005797af5d7d75f652",
                "TransactionID": "REH3SOIU9T",
                "ResultParameters": {
                    "ResultParameter": [
                        {
                            "Key": "ReceiverPartyPublicName",
                            "Value": "254704845040 - WARUI NGUGI",
                        },
                        {
                            "Key": "TransactionCompletedDateTime",
                            "Value": "17.05.2023 22:41:32",
                        },
                        {"Key": "B2CUtilityAccountAvailableFunds", "Value": 5970.0},
                        {"Key": "B2CWorkingAccountAvailableFunds", "Value": 312.74},
                        {"Key": "B2CRecipientIsRegisteredCustomer", "Value": "Y"},
                        {"Key": "B2CChargesPaidAccountAvailableFunds", "Value": 0.0},
                        {"Key": "TransactionAmount", "Value": 10},
                        {"Key": "TransactionReceipt", "Value": "REH3SOIU9T"},
                    ]
                },
                "ReferenceData": {
                    "ReferenceItem": {
                        "Key": "QueueTimeoutURL",
                        "Value": "http://internalapi.safaricom.co.ke/mpesa/b2cresults/v1/submit",
                    }
                },
            }
        }

    @patch("accounts.views.mpesa.process_b2c_payment_result_task.delay")
    def test_white_listed_ip_can_make_post_request(self, mock_task):
        for ip in MPESA_WHITE_LISTED_IPS:
            self.client.defaults["REMOTE_ADDR"] = ip
            response = self.client.post(
                self.url, data=self.sample_successful_b2c_result, format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_white_listed_ip_cannot_make_post_request(self):
        non_white_listed_ip = "192.0.2.1"
        self.client.defaults["REMOTE_ADDR"] = non_white_listed_ip
        response = self.client.post(
            self.url, data=self.sample_successful_b2c_result, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("accounts.views.mpesa.process_b2c_payment_result_task.delay")
    def test_successful_request_triggers_background_task(self, mock_task):
        ip = MPESA_WHITE_LISTED_IPS[0]
        self.client.defaults["REMOTE_ADDR"] = ip
        response = self.client.post(
            self.url, data=self.sample_successful_b2c_result, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_task.assert_called_once()

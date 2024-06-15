from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from commons.throttles import RegisterThrottle
from users.models import User
from users.otp import create_otp


class RegisterViewTestCase(APITestCase):
    @patch("commons.tasks.send_sms.delay")
    def test_register_view(self, send_sms_mock) -> None:
        """Assert registration view creates user."""
        data = {"phone_number": "+254701456761", "password": "passwordAl123"}

        response = self.client.post(reverse("auth:register"), data)

        self.assertEqual(
            response.status_code, 201
        )  # Check if user was created successfully
        self.assertTrue(
            User.objects.filter(phone_number="+254701456761").exists()
        )  # Check if user exists

        send_sms_mock.assert_called_once()  # Check if send_sms was called

        # Check if the correct arguments were passed to send_sms
        call_args = send_sms_mock.call_args
        phone_number, _ = call_args[0]
        self.assertEqual(phone_number, "+254701456761")

    @patch("commons.tasks.send_sms.delay")
    def test_register_view_throttle(self, send_sms_mock):
        """Assert the view throttles requests."""
        data = {"phone_number": "+254701451731", "password": "passwordAl123"}
        for _ in range(10):
            self.client.post(reverse("auth:register"), data)

        # Check that some requests are throttled (HTTP 429 Too Many Requests)
        throttled_response = self.client.post(reverse("auth:register"), data)
        self.assertEqual(
            throttled_response.status_code, status.HTTP_429_TOO_MANY_REQUESTS
        )

        # Clear the throttle cache
        RegisterThrottle.cache.clear()


class AuthTokenTestCase(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            phone_number="+254701456761", password="StrongPassword123", is_active=True
        )

    def test_url_obtains_token_pair_successfully(self) -> None:
        """Assert endpoint returns access and refresh token."""
        url = reverse("auth:obtain-token")
        data = {"phone_number": self.user.phone_number, "password": "StrongPassword123"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.access_token = response.data["access"]
        self.refresh_token = response.data["refresh"]

    def test_url_refreshes_token_successfully(self):
        """Verify that the new access token is different from the old one"""
        # First, obtain a token pair
        self.test_url_obtains_token_pair_successfully()

        url = reverse("auth:refresh-token")
        data = {"refresh": self.refresh_token}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        new_access_token = response.data["access"]
        self.assertNotEqual(self.access_token, new_access_token)

    def test_access_denied_if_user_is_inactive(self):
        """Assert inactive user is denied login access."""
        User.objects.create_user(
            phone_number="+254701436763", password="StrongPassword123", is_active=False
        )
        data = {"phone_number": "+254701436763", "password": "StrongPassword123"}

        response = self.client.post(reverse("auth:obtain-token"), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class OTPVerificationTestCase(APITestCase):
    def setUp(self) -> None:
        self.phone_number = "+254701476761"
        self.user = User.objects.create_user(
            phone_number=self.phone_number,
            password="strong_password",
        )
        self.otp = create_otp(self.phone_number)
        self.url = reverse("auth:verify-otp")

    def test_otp_verifies_user(self) -> None:
        """Assert OTP verifies user."""
        data = {"phone_number": self.phone_number, "otp": self.otp}
        response = self.client.post(self.url, data)
        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "User activated successfully.")
        self.assertTrue(self.user.is_verified)

    def test_invalid_otp_verification_fails(self):
        """"""
        data = {"phone_number": self.phone_number, "otp": "invalid_otp"}
        response = self.client.post(self.url, data)
        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("otp", response.data)
        self.assertFalse(self.user.is_verified)

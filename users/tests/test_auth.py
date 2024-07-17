from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from commons.tests.base_tests import BaseUserAPITestCase
from commons.throttles import AuthenticationThrottle
from users.models import User
from users.otp import create_otp


class RegisterViewTestCase(APITestCase):
    @patch("users.views.auth.send_sms.delay")
    def test_view_creates_user(self, send_sms_mock) -> None:
        """Assert registration view creates user."""
        data = {
            "phone_number": "+254701456761",
            "password": "passwordAl123",
            "is_staff": True,
        }

        response = self.client.post(reverse("auth:register"), data)

        self.assertEqual(
            response.status_code, 201
        )  # Check if user was created successfully
        self.assertTrue(
            User.objects.filter(phone_number="+254701456761").exists()
        )  # Check if user exists

        send_sms_mock.assert_called_once()  # Check if send_sms was called

        # Check if the correct arguments were passed to send_sms
        phone_number = send_sms_mock.call_args.kwargs["phone_number"]

        self.assertTrue(response.data["is_active"])
        self.assertFalse(response.data["is_verified"])
        self.assertNotIn("password", response.data)
        self.assertNotIn("is_staff", response.data)
        self.assertFalse(User.objects.get(phone_number=phone_number).is_staff)
        self.assertEqual(phone_number, "+254701456761")

    @patch("users.views.auth.send_sms.delay")
    def test_view_creates_user_with_national_phone_number(self, send_sms_mock) -> None:
        """Assert registration view creates user with national number."""
        data = {"phone_number": "0701686761", "password": "passwordAl123"}

        response = self.client.post(reverse("auth:register"), data)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(phone_number="+254701686761").exists())

    @patch("users.views.auth.send_sms.delay")
    def test_view_throttles_requests(self, send_sms_mock):
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
        AuthenticationThrottle.cache.clear()


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
        self.assertIn("id", response.data)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.access_token = response.data["access"]
        self.refresh_token = response.data["refresh"]

    def test_url_obtains_token_pair_using_national_number(self) -> None:
        """Assert endpoint standardizes phone number to required format."""
        url = reverse("auth:obtain-token")
        data = {"phone_number": "0701456761", "password": "StrongPassword123"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

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


class ResendOTPVerificationTestCase(BaseUserAPITestCase):
    def setUp(self) -> None:
        self.user = self.create_user()
        self.url = reverse("auth:resend-otp")
        self.data = {"phone_number": str(self.user.phone_number)}

    @patch("users.views.auth.create_otp")
    @patch("users.views.auth.send_sms.delay")
    def test_throttling(self, mock_send_sms, mock_create_otp) -> None:
        for _ in range(20):  # Assuming throttle limit is 5 requests per hour
            response = self.client.post(self.url, self.data, format="json")

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        AuthenticationThrottle.cache.clear()

    @patch("users.views.auth.create_otp")
    @patch("users.views.auth.send_sms.delay")
    def test_user_is_already_verified(self, mock_send_sms, mock_create_otp) -> None:
        self.user.is_verified = True
        self.user.save()

        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("users.views.auth.create_otp")
    @patch("users.views.auth.send_sms.delay")
    def test_user_does_not_exist(self, mock_send_sms, mock_create_otp):
        data = {"phone_number": "+254711111111"}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PasswordResetTestCase(APITestCase):
    def setUp(self):
        self.phone_number = "+254701234567"
        self.user = User.objects.create_user(
            phone_number=self.phone_number, password="StrongPassword123"
        )
        self.password_reset_url = reverse("auth:password-reset-request")
        self.password_reset_confirm_url = reverse("auth:password-reset-confirm")

    @patch("users.views.auth.send_sms.delay")
    def test_view_sends_otp(self, send_sms_mock):
        """Assert view sends OTP to validate user"""
        response = self.client.post(
            self.password_reset_url, {"phone_number": self.user.phone_number}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        send_sms_mock.assert_called_once()
        self.assertEqual(
            response.data["detail"], "OTP has been sent to your phone number."
        )

    def test_view_resets_password(self):
        """Assert the updates the password"""
        new_password = "NewStrongPassword123"
        otp = create_otp(self.phone_number)

        response = self.client.post(
            self.password_reset_confirm_url,
            {
                "phone_number": "0701234567",
                "otp": otp,
                "new_password": new_password,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify that the password has actually been changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))

    def test_view_fails_to_reset_password(self):
        """Assert view fails to reset the password if OTP is invalid."""
        new_password = "NewStrongPassword123"

        response = self.client.post(
            self.password_reset_confirm_url,
            {
                "phone_number": self.phone_number,
                "otp": "wrong_otp",
                "new_password": new_password,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

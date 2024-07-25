# tests/test_views.py
from datetime import datetime
from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse
from rest_framework import status

from commons.constants import SessionCategories
from commons.errors import ErrorCodes
from commons.tests.base_tests import BaseUserAPITestCase


class BusinessHoursViewTests(BaseUserAPITestCase):
    def setUp(self) -> None:
        self.force_authenticate_user()
        self.url = reverse("sessions:business-hours")

    @patch("commons.utils.datetime")
    @override_settings(BUSINESS_IS_OPEN=True)
    def test_business_is_open(self, mock_datetime) -> None:
        """Assert that if setting is True, business opens automatically."""
        # Mock the current time to be within business hours
        mock_datetime.now.return_value = datetime(2024, 7, 22, 11, 0)
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_open"])

    @override_settings(BUSINESS_IS_OPEN=False)
    def test_business_is_closed(self) -> None:
        """Assert that if setting is False, business is closed throughout the day.."""
        with patch("commons.utils.datetime") as mock_datetime:
            # Mock the current time to be within business hours
            mock_datetime.now.return_value = datetime(2024, 7, 22, 11, 0)
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            response = self.client.get(self.url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertFalse(response.data["is_open"])

    @patch("commons.utils.datetime")
    def test_business_closed_before_opening_time(self, mock_datetime) -> None:
        # Mock the current time to be before business hours
        mock_datetime.now.return_value = datetime(2024, 7, 22, 7, 0)
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_open"])

    @patch("commons.utils.datetime")
    def test_business_closed_after_closing_time(self, mock_datetime) -> None:
        # Mock the current time to be after business hours
        mock_datetime.now.return_value = datetime(2024, 7, 22, 18, 0)
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_open"])


class SessionDetailsViewTest(BaseUserAPITestCase):
    def setUp(self) -> None:
        self.force_authenticate_user()
        self.url = reverse("sessions:details")

    def test_get_session_details(self) -> None:
        expected_data = {"questions": 5, "seconds": 30, "stake": 50, "payout": 87}

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)


class AvailableSessionViewTests(BaseUserAPITestCase):
    def setUp(self) -> None:
        self.force_authenticate_user()
        self.url = reverse(
            "sessions:available-session"
        )  # Adjust the URL name as needed
        self.valid_payload = {"category": SessionCategories.FOOTBALL.value}
        self.invalid_payload = {"category": "INVALID_CATEGORY"}

    @patch("user_sessions.views.sessions.get_available_session")
    def test_view_returns_id_when_session_available(self, mock_get_available_session):
        mock_get_available_session.return_value = "some_session_id"

        response = self.client.post(self.url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("id", response.data)
        self.assertEqual(response.data["id"], "some_session_id")

    @patch("user_sessions.views.sessions.get_available_session")
    def test_view_raises_error_when_no_session_available(
        self, mock_get_available_session
    ):
        mock_get_available_session.return_value = None
        response = self.client.post(self.url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
        self.assertEqual(response.data["detail"], ErrorCodes.NO_AVAILABLE_SESSION.value)

    def test_view_raises_error_with_invalid_category(self):
        response = self.client.post(self.url, self.invalid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("category", response.data)

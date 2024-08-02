# tests/test_views.py
from datetime import datetime
from unittest.mock import patch

from django.conf import settings
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from rest_framework import status

from commons.constants import DuoSessionStatuses, SessionCategories
from commons.errors import ErrorCodes
from commons.tests.base_tests import BaseUserAPITestCase
from user_sessions.models import DuoSession, Session


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
        expected_data = {"questions": 5, "seconds": 20, "stake": 50, "payout": 87}

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

        self.cache_key = f"{self.user.id}:available_session_id"

    @patch("user_sessions.views.sessions.get_available_session")
    def test_view_returns_id_when_session_available(self, mock_get_available_session):
        mock_get_available_session.return_value = "some_session_id"

        response = self.client.post(self.url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("id", response.data)
        self.assertEqual(response.data["id"], "some_session_id")

        cached_value = cache.get(self.cache_key)
        self.assertEqual(cached_value, "some_session_id")

    @patch("user_sessions.views.sessions.get_available_session")
    def test_view_raises_error_when_no_session_available(
        self, mock_get_available_session
    ):
        mock_get_available_session.return_value = None
        response = self.client.post(self.url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
        self.assertEqual(response.data["detail"], ErrorCodes.NO_AVAILABLE_SESSION.value)

        cached_value = cache.get(self.cache_key)
        self.assertIsNone(cached_value)

    def test_view_raises_error_with_invalid_category(self):
        response = self.client.post(self.url, self.invalid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("category", response.data)

        cached_value = cache.get(self.cache_key)
        self.assertIsNone(cached_value)


class DuoSessionListViewTestCase(BaseUserAPITestCase):
    def setUp(self) -> None:
        self.user = self.create_user()
        self.foreign_user = self.create_foreign_user()

        self.session = Session.objects.create(category=SessionCategories.BIBLE.value)
        self.refunded_duo_session = DuoSession.objects.create(
            party_a=self.user,
            session=self.session,
            amount=settings.SESSION_STAKE,
            status=DuoSessionStatuses.REFUNDED.value,
        )
        self.partially_refunded_duo_session = DuoSession.objects.create(
            party_a=self.foreign_user,
            session=self.session,
            amount=settings.SESSION_STAKE,
            status=DuoSessionStatuses.PARTIALLY_REFUNDED.value,
        )
        self.paired_duo_session = DuoSession.objects.create(
            party_a=self.foreign_user,
            party_b=self.user,
            session=self.session,
            amount=settings.SESSION_STAKE,
            status=DuoSessionStatuses.PAIRED.value,
            winner=self.user,
        )

        self.force_authenticate_staff_user()
        self.list_url = reverse("sessions:duo-session-list")

    def test_staff_can_list_duo_sessions(self) -> None:
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)

    def test_staff_can_search_duo_sessions(self) -> None:
        response = self.client.get(
            self.list_url, {"search": str(self.foreign_user.phone_number)}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_user_can_list_their_own_duo_sessions(self) -> None:
        self.force_authenticate_user()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertEqual(
            response.data["results"][0]["id"],
            str(self.paired_duo_session.id),
        )

    def test_staff_fields_do_not_exist_in_response(self) -> None:
        self.force_authenticate_user()
        response = self.client.get(self.list_url)
        result_in = response.data["results"][0]
        self.assertNotIn("party_a", result_in)
        self.assertNotIn("party_b", result_in)
        self.assertNotIn("winner", result_in)

    def test_user_can_search_duo_sessions(self) -> None:
        response = self.client.get(
            self.list_url, {"search": str(self.paired_duo_session.id)}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["id"],
            str(self.paired_duo_session.id),
        )

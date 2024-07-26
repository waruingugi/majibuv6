# tests/test_views.py
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

from django.conf import settings
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from rest_framework import status

from accounts.constants import (
    TransactionCashFlow,
    TransactionServices,
    TransactionStatuses,
    TransactionTypes,
)
from accounts.models import Transaction
from commons.constants import SessionCategories
from commons.errors import ErrorCodes
from commons.tests.base_tests import BaseUserAPITestCase
from commons.utils import md5_hash
from quiz.models import Result
from user_sessions.constants import AVAILABLE_SESSION_EXPIRY_TIME
from user_sessions.models import Session
from user_sessions.tests.test_data import mock_compoze_quiz_return_data


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


class QuizViewTests(BaseUserAPITestCase):
    def setUp(self):
        self.force_authenticate_user()
        self.session = Session.objects.create(
            category=SessionCategories.FOOTBALL.value, _questions="q1,q2,q3,q4,q5"
        )
        self.url = reverse("sessions:quiz")

    def tearDown(self):
        cache.clear()  # Clear cache after each test to ensure isolation

    @patch("user_sessions.serializers.is_business_open", return_value=True)
    @patch(
        "user_sessions.serializers.Transaction.objects.get_user_balance",
        return_value=100,
    )
    @patch(
        "user_sessions.views.sessions.compose_quiz",
        return_value=mock_compoze_quiz_return_data,
    )
    def test_view_returns_correct_response(
        self, mock_compose_quiz, mock_get_user_balance, mock_is_business_open
    ):
        cache.set(
            f"{self.user.id}:available_session_id",
            str(self.session.id),
            timeout=AVAILABLE_SESSION_EXPIRY_TIME,
        )

        response = self.client.post(self.url, data={"session_id": self.session.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["session_id"], str(self.session.id))
        self.assertEqual(response.data["user_id"], str(self.user.id))
        self.assertEqual(response.data["count"], settings.QUESTIONS_IN_SESSION)
        self.assertIn("result", response.data)

    @patch("user_sessions.serializers.is_business_open", return_value=True)
    @patch(
        "user_sessions.views.sessions.compose_quiz",
        return_value=mock_compoze_quiz_return_data,
    )
    def test_view_deducts_session_amount_from_wallet(
        self, mock_compose_quiz, mock_is_business_open
    ):
        cache.set(
            f"{self.user.id}:available_session_id",
            str(self.session.id),
            timeout=AVAILABLE_SESSION_EXPIRY_TIME,
        )
        self.transaction = Transaction.objects.create(
            external_transaction_id="TX12345678",
            initial_balance=Decimal("0.0"),
            final_balance=Decimal("100.0"),
            cash_flow=TransactionCashFlow.INWARD.value,
            type=TransactionTypes.DEPOSIT.value,
            amount=Decimal("100.00"),
            fee=Decimal("0.00"),
            tax=Decimal("0.00"),
            charge=Decimal("00.00"),
            status=TransactionStatuses.SUCCESSFUL.value,
            service=TransactionServices.MPESA.value,
            description="Test Description",
            user=self.user,
        )

        self.client.post(self.url, data={"session_id": self.session.id})
        self.assertEqual(50.0, float(Transaction.objects.get_user_balance(self.user)))

    @patch("user_sessions.serializers.is_business_open", return_value=True)
    @patch(
        "user_sessions.serializers.Transaction.objects.get_user_balance",
        return_value=100,
    )
    def test_view_fails_for_invalid_session_id(
        self, mock_get_user_balance, mock_is_business_open
    ):
        response = self.client.post(self.url, data={"session_id": "invalid-id"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["detail"][0]), ErrorCodes.INVALID_SESSION_ID.value
        )

    @patch("user_sessions.serializers.is_business_open", return_value=False)
    @patch(
        "user_sessions.serializers.Transaction.objects.get_user_balance",
        return_value=100,
    )
    def test_view_fails_when_business_closed(
        self, mock_get_user_balance, mock_is_business_open
    ):
        cache.set(
            f"{self.user.id}:available_session_id",
            str(self.session.id),
            timeout=AVAILABLE_SESSION_EXPIRY_TIME,
        )
        response = self.client.post(self.url, data={"session_id": self.session.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["detail"][0]), ErrorCodes.BUSINESS_IS_CLOSED.value
        )

    @patch("user_sessions.serializers.is_business_open", return_value=True)
    @patch(
        "user_sessions.serializers.Transaction.objects.get_user_balance",
        return_value=100,
    )
    def test_view_fails_when_withdrawal_request_in_queue(
        self, mock_get_user_balance, mock_is_business_open
    ):
        cache.set(
            md5_hash(f"{self.user.phone_number}:withdraw_request"), True, timeout=60
        )
        cache.set(
            f"{self.user.id}:available_session_id",
            str(self.session.id),
            timeout=AVAILABLE_SESSION_EXPIRY_TIME,
        )
        response = self.client.post(self.url, data={"session_id": self.session.id})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["detail"][0]),
            ErrorCodes.WITHDRAWAL_REQUEST_IN_QUEUE.value,
        )

    @patch("user_sessions.serializers.is_business_open", return_value=True)
    @patch(
        "user_sessions.serializers.Transaction.objects.get_user_balance",
        return_value=10,
    )
    def test_view_fails_if_user_has_insufficient_balance(
        self, mock_get_user_balance, mock_is_business_open
    ):
        cache.set(
            f"{self.user.id}:available_session_id",
            str(self.session.id),
            timeout=AVAILABLE_SESSION_EXPIRY_TIME,
        )
        response = self.client.post(self.url, data={"session_id": self.session.id})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["detail"][0]),
            ErrorCodes.INSUFFICIENT_BALANCE_TO_WITHDRAW.value.format(
                settings.SESSION_STAKE
            ),
        )

    @patch("user_sessions.serializers.is_business_open", return_value=True)
    @patch(
        "user_sessions.serializers.Transaction.objects.get_user_balance",
        return_value=100,
    )
    def test_view_fails_if_active_session_exists(
        self, mock_get_user_balance, mock_is_business_open
    ):
        Result.objects.create(
            user=self.user,
            session=self.session,
            is_active=True,
            expires_at=datetime.now(),
        )
        cache.set(
            f"{self.user.id}:available_session_id",
            str(self.session.id),
            timeout=AVAILABLE_SESSION_EXPIRY_TIME,
        )
        response = self.client.post(self.url, data={"session_id": self.session.id})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["detail"][0]), ErrorCodes.SESSION_IN_QUEUE.value
        )

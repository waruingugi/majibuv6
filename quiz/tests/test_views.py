from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

from django.conf import settings
from django.core.cache import cache
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


class QuizViewTests(BaseUserAPITestCase):
    def setUp(self):
        self.force_authenticate_user()
        self.session = Session.objects.create(
            category=SessionCategories.FOOTBALL.value, _questions="q1,q2,q3,q4,q5"
        )
        self.url = reverse("quiz:request-quiz")

    def tearDown(self):
        cache.clear()  # Clear cache after each test to ensure isolation

    @patch("quiz.serializers.is_business_open", return_value=True)
    @patch(
        "quiz.serializers.Transaction.objects.get_user_balance",
        return_value=100,
    )
    @patch(
        "quiz.views.quiz.compose_quiz",
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

    @patch("quiz.serializers.is_business_open", return_value=True)
    @patch(
        "quiz.views.quiz.compose_quiz",
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

    @patch("quiz.serializers.is_business_open", return_value=True)
    @patch(
        "quiz.serializers.Transaction.objects.get_user_balance",
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

    @patch("quiz.serializers.is_business_open", return_value=False)
    @patch(
        "quiz.serializers.Transaction.objects.get_user_balance",
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

    @patch("quiz.serializers.is_business_open", return_value=True)
    @patch(
        "quiz.serializers.Transaction.objects.get_user_balance",
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

    @patch("quiz.serializers.is_business_open", return_value=True)
    @patch(
        "quiz.serializers.Transaction.objects.get_user_balance",
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

    @patch("quiz.serializers.is_business_open", return_value=True)
    @patch(
        "quiz.serializers.Transaction.objects.get_user_balance",
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


class QuizSubmissionViewTests(BaseUserAPITestCase):
    def setUp(self):
        self.force_authenticate_user()
        self.url = reverse("quiz:submit-quiz")
        self.valid_payload = {
            "result_id": "result123",
            "choices": [
                {"question_id": "11", "choice": "A"},
                {"question_id": "22", "choice": "B"},
                {"question_id": "33", "choice": "C"},
            ],
        }
        self.payload_with_missing_choices = {
            "result_id": "result123",
            "choices": [
                {"question_id": "11", "choice": "A"},
                {"question_id": "22", "choice": ""},
                {"question_id": "33", "choice": ""},
            ],
        }
        self.invalid_payload = {
            "result_id": "",
            "choices": [
                {"question_id": "1", "choice": "A"},
                {"question_id": "2", "choice": "B"},
                {"question_id": "3", "choice": ""},
            ],
        }

    @patch("quiz.views.quiz.CalculateUserScore.calculate_score")
    def test_quiz_submission_with_all_choices_is_successfull(
        self, mock_calculate_score
    ):
        mock_calculate_score.return_value = None  # Mock the return value if necessary
        response = self.client.post(self.url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Choices submitted successfully")
        mock_calculate_score.assert_called_once_with(
            user=self.user,
            result_id=self.valid_payload["result_id"],
            choices=self.valid_payload["choices"],
        )

    @patch("quiz.views.quiz.CalculateUserScore.calculate_score")
    def test_quiz_submission_with_missing_choices_is_successfull(
        self, mock_calculate_score
    ):
        mock_calculate_score.return_value = None  # Mock the return value if necessary
        response = self.client.post(self.url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Choices submitted successfully")
        mock_calculate_score.assert_called_once_with(
            user=self.user,
            result_id=self.valid_payload["result_id"],
            choices=self.valid_payload["choices"],
        )

    @patch("quiz.views.quiz.CalculateUserScore.calculate_score")
    def test_quiz_submission_invalid_data(self, mock_calculate_score):
        response = self.client.post(self.url, self.invalid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_calculate_score.assert_not_called()

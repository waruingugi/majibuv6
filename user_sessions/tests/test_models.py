from decimal import Decimal

from django.conf import settings
from django.test import TestCase

from accounts.constants import TransactionTypes
from accounts.models import Transaction
from commons.constants import DuoSessionStatuses, SessionCategories
from commons.tests.base_tests import BaseUserAPITestCase
from user_sessions.models import DuoSession, PoolSessionStat, Session, UserSessionStat


class UserSessionStatModelTest(BaseUserAPITestCase):
    def setUp(self):
        self.user = self.create_user()
        self.stats = UserSessionStat.objects.create(
            user=self.user, total_wins=5, total_losses=3, sessions_played=8
        )

    def test_user_session_stats_creation(self):
        """Test if a UserSessionStat instance is created correctly."""
        self.assertEqual(self.stats.user, self.user)
        self.assertEqual(self.stats.total_wins, 5)
        self.assertEqual(self.stats.total_losses, 3)
        self.assertEqual(self.stats.sessions_played, 8)

    def test_user_session_stats_win_ratio(self):
        """Test the calculation of the win_ratio property."""
        self.assertEqual(self.stats.win_ratio, 5 / 8)

    def test_user_session_stats_win_ratio_zero_sessions(self):
        """Test the win_ratio property when sessions_played is zero."""
        self.stats.sessions_played = 0
        self.stats.save()
        updated_stats = UserSessionStat.objects.get(id=self.stats.id)
        self.assertEqual(updated_stats.win_ratio, 0.0)

    def test_update_user_session_stats(self):
        """Test updating the UserSessionStats fields."""
        self.stats.total_wins = 10
        self.stats.total_losses = 5
        self.stats.sessions_played = 15
        self.stats.save()
        updated_stats = UserSessionStat.objects.get(id=self.stats.id)
        self.assertEqual(updated_stats.total_wins, 10)
        self.assertEqual(updated_stats.total_losses, 5)
        self.assertEqual(updated_stats.sessions_played, 15)
        self.assertEqual(updated_stats.win_ratio, 10 / 15)

    def test_user_session_stats_no_division_by_zero(self):
        """Test that the win_ratio property does not raise a division by zero error."""
        self.stats.sessions_played = 0
        self.stats.save()
        updated_stats = UserSessionStat.objects.get(id=self.stats.id)
        try:
            _ = updated_stats.win_ratio
        except ZeroDivisionError:
            self.fail("win_ratio() raised ZeroDivisionError unexpectedly!")


class SessionModelTest(TestCase):
    def setUp(self):
        self.category = SessionCategories.FOOTBALL.value
        self.session = Session.objects.create(
            category=self.category, _questions="question1, question2, question3"
        )

    def test_sessions_creation(self):
        """Test if a Sessions instance is created correctly."""
        self.assertEqual(self.session.category, self.category)
        self.assertEqual(self.session._questions, "question1, question2, question3")

    def test_sessions_questions_property(self):
        """Test the questions property."""
        expected_questions = ["question1", "question2", "question3"]
        self.assertEqual(self.session.questions, expected_questions)

    def test_sessions_questions_property_with_spaces(self):
        """Test the questions property with spaces in the _questions field."""
        session_with_spaces = Session.objects.create(
            category=self.category, _questions=" question1 , question2 , question3 "
        )
        expected_questions_with_spaces = ["question1", "question2", "question3"]
        self.assertEqual(session_with_spaces.questions, expected_questions_with_spaces)

    def test_sessions_str_method(self):
        """Test the __str__ method of the Sessions model."""
        self.assertEqual(str(self.session), self.category)


class DuoSessionModelTest(BaseUserAPITestCase):
    def setUp(self) -> None:
        self.user = self.create_user()
        self.foreign_user = self.create_foreign_user()

        self.session = Session.objects.create(
            category=SessionCategories.FOOTBALL.value,
            _questions="question1, question2, question3",
        )
        self.refunded_duo_session = DuoSession.objects.create(
            party_a=self.user,
            session=self.session,
            amount=settings.SESSION_STAKE,
            status=DuoSessionStatuses.REFUNDED.value,
        )

        self.partially_refunded_duo_session = DuoSession.objects.create(
            party_a=self.user,
            session=self.session,
            amount=settings.SESSION_STAKE,
            status=DuoSessionStatuses.PARTIALLY_REFUNDED.value,
        )

    def tearDown(self) -> None:
        """Run after each test"""
        Transaction.objects.all().delete()

    def test_duo_session_creates_a_partially_refunded_sesssion(self) -> None:
        """Test if a partially refunded DuoSession instance is created correctly."""
        self.assertEqual(self.partially_refunded_duo_session.party_a, self.user)
        self.assertEqual(self.partially_refunded_duo_session.session, self.session)
        self.assertEqual(
            self.partially_refunded_duo_session.amount, settings.SESSION_STAKE
        )
        self.assertEqual(
            self.partially_refunded_duo_session.status,
            DuoSessionStatuses.PARTIALLY_REFUNDED.value,
        )
        self.assertEqual(
            self.partially_refunded_duo_session.category,
            SessionCategories.FOOTBALL.value,
        )

        self.assertTrue(
            Transaction.objects.filter(
                type=TransactionTypes.REFUND.value,
                amount=Decimal(
                    settings.SESSION_PARTIAL_REFUND_RATIO * settings.SESSION_STAKE
                ),
            ).exists()
        )

    def test_duo_session_creates_a_refunded_sesssion(self) -> None:
        """Test if a refunded DuoSession instance is created correctly."""
        self.assertEqual(self.refunded_duo_session.party_a, self.user)
        self.assertEqual(self.refunded_duo_session.session, self.session)
        self.assertEqual(self.refunded_duo_session.amount, settings.SESSION_STAKE)
        self.assertEqual(
            self.refunded_duo_session.status, DuoSessionStatuses.REFUNDED.value
        )
        self.assertEqual(
            self.refunded_duo_session.category, SessionCategories.FOOTBALL.value
        )

        self.assertTrue(
            Transaction.objects.filter(
                type=TransactionTypes.REFUND.value,
                amount=Decimal(settings.SESSION_REFUND_RATIO * settings.SESSION_STAKE),
            ).exists()
        )

    def test_duo_session_creates_a_paired_sesssion(self) -> None:
        """Test if a paired DuoSession instance is created correctly."""
        session = Session.objects.create(
            category=SessionCategories.FOOTBALL.value,
            _questions="q6, q7, q8, q9",
        )
        paired_duo_session = DuoSession.objects.create(
            party_a=self.foreign_user,
            party_b=self.user,
            session=session,
            amount=settings.SESSION_STAKE,
            status=DuoSessionStatuses.PAIRED.value,
            winner=self.user,
        )
        self.assertEqual(paired_duo_session.party_a, self.foreign_user)
        self.assertEqual(paired_duo_session.winner, self.user)
        self.assertEqual(paired_duo_session.status, DuoSessionStatuses.PAIRED.value)

        self.assertTrue(
            Transaction.objects.filter(
                type=TransactionTypes.REWARD.value,
                amount=Decimal(settings.SESSION_WIN_RATIO * settings.SESSION_STAKE),
            ).exists()
        )


class PoolSessionStatModelTest(TestCase):
    def setUp(self):
        self.pool_session_stats = PoolSessionStat.objects.create(
            total_players=10, _statistics='{"average_score": 75.5}'
        )

    def test_pool_session_stats_creation(self):
        """Test if a PoolSessionStats instance is created correctly."""
        self.assertEqual(self.pool_session_stats.total_players, 10)
        self.assertEqual(self.pool_session_stats._statistics, '{"average_score": 75.5}')

    def test_pool_session_stats_statistics_property(self):
        """Test the statistics property."""
        expected_statistics = {"average_score": 75.5}
        self.assertEqual(self.pool_session_stats.statistics, expected_statistics)

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from django.conf import settings

from commons.constants import DuoSessionStatuses, SessionCategories
from commons.tests.base_tests import BaseQuizTestCase
from quiz.models import Result
from quiz.user_pairing import PairingService
from user_sessions.constants import SESSION_BUFFER_TIME
from user_sessions.models import DuoSession
from users.models import User


class PairUsersTestCase(BaseQuizTestCase):
    def setUp(self) -> None:
        """Set up initial test data"""
        super().setUp()
        self.pair_users = PairingService
        self.create_test_data()

    def create_test_data(self) -> None:
        """Create test data for the Result model"""
        # Create some test results
        for i in range(9):
            user = User.objects.create(phone_number=f"+2547080800{i}")
            Result.objects.create(
                user=user,
                score=i * 10,
                expires_at=datetime.now()
                + timedelta(seconds=(SESSION_BUFFER_TIME + settings.SESSION_DURATION)),
                session=self.session,
            )

    def tearDown(self) -> None:
        """Run after each test."""
        Result.objects.all().delete()

    def test_get_exclusions_excludes_results(self) -> None:
        """Test the get_exclusions method"""
        results = Result.objects.filter(session__category=self.category).order_by(
            "score"
        )
        bottom_exclusion_count = 2
        top_exclusion_count = 2

        to_pair, to_exclude = self.pair_users.get_exclusions(
            results, bottom_exclusion_count, top_exclusion_count
        )
        results_list = list(results)

        self.assertEqual(len(to_exclude), bottom_exclusion_count + top_exclusion_count)
        self.assertEqual(
            len(to_pair),
            results.count() - (bottom_exclusion_count + top_exclusion_count),
        )
        self.assertListEqual(
            list(to_exclude),
            list(results_list[:bottom_exclusion_count])
            + list(results_list[-top_exclusion_count:]),
        )
        self.assertListEqual(
            list(to_pair),
            list(results_list[bottom_exclusion_count:-top_exclusion_count]),
        )

    def test_dynamic_exclusion_percentages_positive_skew(self) -> None:
        (
            bottom_exclusion_count,
            top_exclusion_count,
        ) = self.pair_users.dynamic_exclusion_percentages(1, 100)
        self.assertEqual(bottom_exclusion_count, 5)
        self.assertEqual(top_exclusion_count, 15)

    def test_dynamic_exclusion_percentages_negative_skew(self) -> None:
        (
            bottom_exclusion_count,
            top_exclusion_count,
        ) = self.pair_users.dynamic_exclusion_percentages(-1, 100)
        self.assertEqual(bottom_exclusion_count, 15)
        self.assertEqual(top_exclusion_count, 5)

    def test_dynamic_exclusion_percentages_no_skew(self) -> None:
        (
            bottom_exclusion_count,
            top_exclusion_count,
        ) = self.pair_users.dynamic_exclusion_percentages(0, 100)
        self.assertEqual(bottom_exclusion_count, 10)
        self.assertEqual(top_exclusion_count, 10)

    def test_dynamic_exclusion_percentages_normalization(self) -> None:
        (
            bottom_exclusion_count,
            top_exclusion_count,
        ) = self.pair_users.dynamic_exclusion_percentages(0.5, 100)
        self.assertEqual(bottom_exclusion_count, 7)
        self.assertEqual(top_exclusion_count, 12)

    def test_dynamic_exclusion_percentages_high_positive_skew(self) -> None:
        (
            bottom_exclusion_count,
            top_exclusion_count,
        ) = self.pair_users.dynamic_exclusion_percentages(4, 100)
        self.assertAlmostEqual(bottom_exclusion_count, 0, places=1)
        self.assertAlmostEqual(top_exclusion_count, 20, places=1)

    def test_dynamic_exclusion_percentages_high_negative_skew(self) -> None:
        (
            bottom_exclusion_count,
            top_exclusion_count,
        ) = self.pair_users.dynamic_exclusion_percentages(-4, 100)
        self.assertAlmostEqual(bottom_exclusion_count, 20, places=1)
        self.assertAlmostEqual(top_exclusion_count, 0, places=1)

    def test_calculate_skewness_positive(self) -> None:
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 100]  # Right skewed
        results = []
        for value in values:
            result = MagicMock()
            result.score = value
            results.append(result)

        skewness = self.pair_users.calculate_skewness(results)
        self.assertGreater(skewness, 0)  # Expect a positive skew

    def test_calculate_skewness_no_results(self) -> None:
        Result.objects.all().delete()
        Result.objects.create(
            user=self.user,
            expires_at=datetime.now()
            + timedelta(seconds=(SESSION_BUFFER_TIME + settings.SESSION_DURATION)),
            session=self.session,
        )
        results = Result.objects.all().order_by("score")

        skewness = self.pair_users.calculate_skewness(results)
        self.assertEqual(skewness, 0)

    def test_calculate_skewness_negative(self) -> None:
        values = [100, 90, 80, 70, 60, 50, 40, 30, 20, 1]  # Left skewed
        results = []
        for value in values:
            result = MagicMock()
            result.score = value
            results.append(result)

        skewness = self.pair_users.calculate_skewness(results)
        self.assertLess(skewness, 0)  # Expect a negative skew

    def test_calculate_skewness_no_skew(self) -> None:
        values = [50, 51, 49, 50, 50, 51, 49, 50, 50, 50]  # No skew
        results = []
        for value in values:
            result = MagicMock()
            result.score = value
            results.append(result)

        skewness = self.pair_users.calculate_skewness(results)
        self.assertAlmostEqual(skewness, 0, places=1)  # Expect skewness close to zero

    def test_calculate_skewness_uniform(self) -> None:
        values = list(range(1, 101))  # Uniform distribution
        results = []
        for value in values:
            result = MagicMock()
            result.score = value
            results.append(result)

        skewness = self.pair_users.calculate_skewness(results)
        self.assertAlmostEqual(
            skewness, 0, places=1
        )  # Expect skewness close to zero for uniform distribution

    def test_reorder_by_score(self) -> None:
        """Assert first result instance based on score is the lowest score possible."""
        first_result = Result.objects.filter(user=self.user).first()
        results = Result.objects.filter(is_active=True)
        reordered_results = self.pair_users.reorder_by_score(results)

        self.assertEqual(list(reordered_results)[0], first_result)

    def test_get_category_queue(self) -> None:
        """Assert the first result instance is the one created in BaseQuizTestCase."""
        results = self.pair_users.get_category_queue(SessionCategories.FOOTBALL.value)
        results_list = list(results)
        user_result = Result.objects.get(user=self.user)
        # Check if results are ordered by exits_at
        self.assertEqual(results_list[0], user_result)

    def test_is_ready_for_pairing_passed_exits_at(self) -> None:
        """
        Test if is_ready_for_pairing returns True when exits_at is in the past.
        """
        past_time = datetime.now() - timedelta(minutes=1)
        result = Result.objects.create(
            user=self.user,
            exits_at=past_time,
            session=self.session,
            expires_at=datetime.now(),
        )
        self.assertTrue(self.pair_users.is_ready_for_pairing(result))

    def test_is_ready_for_pairing_within_five_minutes(self) -> None:
        """
        Test if is_ready_for_pairing returns True when exits_at is within the next 5 minutes.
        """
        future_time_within_5_minutes = datetime.now() - timedelta(minutes=4)
        result = Result.objects.create(
            user=self.user,
            exits_at=future_time_within_5_minutes,
            session=self.session,
            expires_at=datetime.now(),
        )
        self.assertTrue(self.pair_users.is_ready_for_pairing(result))

    def test_is_ready_for_pairing_outside_five_minutes(self) -> None:
        """
        Test if is_ready_for_pairing returns False when exits_at is more than 5 minutes in the future.
        """
        future_time_outside_5_minutes = datetime.now() + timedelta(minutes=10)
        result = Result.objects.create(
            user=self.user,
            exits_at=future_time_outside_5_minutes,
            session=self.session,
            expires_at=datetime.now(),
        )
        self.assertFalse(self.pair_users.is_ready_for_pairing(result))

    def test_is_ready_for_pairing_just_now(self) -> None:
        """
        Test if is_ready_for_pairing returns True when exits_at is exactly now.
        """
        now = datetime.now()
        result = Result.objects.create(
            user=self.user,
            exits_at=now,
            session=self.session,
            expires_at=datetime.now(),
        )
        self.assertTrue(self.pair_users.is_ready_for_pairing(result))

    def test_is_ready_for_pairing_edge_case_5_minutes(self) -> None:
        """
        Test if is_ready_for_pairing returns True when exits_at is exactly 5 minutes from now.
        """
        future_time_exact_5_minutes = datetime.now() + timedelta(minutes=5)
        result = Result.objects.create(
            user=self.user,
            exits_at=future_time_exact_5_minutes,
            session=self.session,
            expires_at=datetime.now(),
        )
        self.assertTrue(self.pair_users.is_ready_for_pairing(result))

    def test_is_partial_refund_no_answers(self) -> None:
        """
        Test if is_partial_refund returns True when total_answered is 0.
        """
        result = Result.objects.create(
            user=self.user,
            total_answered=0,
            session=self.session,
            expires_at=datetime.now(),
        )
        self.assertTrue(self.pair_users.is_partial_refund(result))

    def test_is_partial_refund_some_answers(self) -> None:
        """
        Test if is_partial_refund returns True even when total_answered is greater than 0.
        """
        result = Result.objects.create(
            user=self.user,
            session=self.session,
            expires_at=datetime.now(),
            total_answered=1,
        )
        self.assertFalse(self.pair_users.is_partial_refund(result))

    def test_is_partial_refund_multiple_answers(self) -> None:
        """
        Test if is_partial_refund returns True even when total_answered is greater than 1.
        """
        result = Result.objects.create(
            user=self.user,
            session=self.session,
            expires_at=datetime.now(),
            total_answered=5,
        )
        self.assertFalse(self.pair_users.is_partial_refund(result))

    def test_is_full_refund_past_exits_at(self) -> None:
        """
        Test if is_full_refund returns True when exits_at is in the past.
        """
        past_time = datetime.now() - timedelta(minutes=1)
        result = Result.objects.create(
            user=self.user,
            session=self.session,
            expires_at=datetime.now(),
            exits_at=past_time,
        )
        self.pair_users.to_exclude = []
        self.assertTrue(self.pair_users.is_full_refund(result))

    def test_is_full_refund_in_to_exclude(self) -> None:
        """
        Test if is_full_refund returns True when result is in to_exclude.
        """
        future_time = datetime.now() + timedelta(minutes=5)
        result = Result.objects.create(
            user=self.user,
            session=self.session,
            expires_at=datetime.now(),
            exits_at=future_time,
        )
        self.pair_users.to_exclude = [result]
        self.assertTrue(self.pair_users.is_full_refund(result))

    def test_is_full_refund_not_in_to_exclude_and_future_exits_at(self) -> None:
        """
        Test if is_full_refund returns False when result is not in to_exclude and exits_at is in the future.
        """
        future_time = datetime.now() + timedelta(minutes=5)
        result = Result.objects.create(
            user=self.user,
            session=self.session,
            expires_at=datetime.now(),
            exits_at=future_time,
        )
        self.pair_users.to_exclude = []
        self.assertFalse(self.pair_users.is_full_refund(result))

    @patch("quiz.user_pairing.PairUsers.have_been_paired_recently", return_value=False)
    def test_find_closest_instance_normal_case(
        self, mock_have_been_paired_recently
    ) -> None:
        """Test returns closest instance on normal cases"""
        self.pair_users.to_exclude = []
        target_instance, instance1, instance2 = (
            MagicMock(Result),
            MagicMock(Result),
            MagicMock(Result),
        )

        target_instance.score = 10
        instance1.score = 8
        instance2.score = 12

        instances = [instance1, instance2]

        # Test method
        closest_instance = self.pair_users.find_closest_instance(
            target_instance, instances
        )
        self.assertEqual(closest_instance, instance1)  # instance1 is closer to score 10

    def test_find_closest_instance_no_instances(self) -> None:
        """Assert None is returned when no other close instances are available."""
        target_instance = MagicMock(Result)
        target_instance.score = 10
        instances: list = []

        closest_instance = self.pair_users.find_closest_instance(
            target_instance, instances
        )
        self.assertIsNone(closest_instance)

    def test_find_closest_instance_same_score(self) -> None:
        """Assert closest instance returns None when closest instance has same score."""
        target_instance, instance1 = MagicMock(Result), MagicMock(Result)

        target_instance.score = 10
        instance1.score = 10
        instances = [instance1]

        closest_instance = self.pair_users.find_closest_instance(
            target_instance, instances
        )
        self.assertIsNone(closest_instance)  # The same score should result in exclusion

    def test_find_closest_instance_exclusion(self) -> None:
        """Assert closest instance is None if it is in to_exclude."""
        target_instance, instance1, instance2 = (
            MagicMock(Result),
            MagicMock(Result),
            MagicMock(Result),
        )

        target_instance.score = 10
        instance1.score = 8
        instance2.score = 11

        self.pair_users.to_exclude = [instance2]  # Set instance2 to be excluded

        instances = [instance1, instance2]

        closest_instance = self.pair_users.find_closest_instance(
            target_instance, instances
        )
        self.assertIsNone(closest_instance)

    @patch("quiz.user_pairing.PairUsers.have_been_paired_recently", return_value=False)
    def test_find_closest_instance_on_two_players_only(
        self, mock_have_been_paired_recently
    ) -> None:
        """Assert closest instance is None if it is in to_exclude."""
        target_instance, instance1 = (MagicMock(Result), MagicMock(Result))

        target_instance.score = 10
        instance1.score = 8
        self.pair_users.to_exclude = []

        instances = [instance1]

        closest_instance = self.pair_users.find_closest_instance(
            target_instance, instances
        )
        self.assertEqual(instance1, closest_instance)

    def test_find_closest_instance_same_user(self) -> None:
        """Assert if closest instance is the same user, then closest instance becomes None."""
        target_instance, instance1 = MagicMock(Result), MagicMock(Result)

        target_instance.score = 10
        instance1.score = 8
        target_instance.user = self.user
        instance1.user = target_instance.user  # Same user as target_instance

        instances = [instance1]

        closest_instance = self.pair_users.find_closest_instance(
            target_instance, instances
        )
        self.assertIsNone(closest_instance)  # Same user should result in exclusion

    def test_find_closest_instance_no_question_answered(self) -> None:
        """Assert closest instance is None if closest instance did not answere any questions."""
        target_instance, instance1 = (MagicMock(Result), MagicMock(Result))

        target_instance.score = 10
        instance1.score = 8
        instance1.total_answered = 0

        self.pair_users.to_exclude = []  # Set instance2 to be excluded

        instances = [instance1, instance1]

        closest_instance = self.pair_users.find_closest_instance(
            target_instance, instances
        )
        self.assertIsNone(closest_instance)


class HaveBeenPairedRecentlyTestCase(BaseQuizTestCase):
    def setUp(self):
        super().setUp()
        self.pair_users = PairingService

        # Create DuoSession instances
        two_hours_ago = datetime.now() - timedelta(hours=1, minutes=45)
        self.duo_session = DuoSession.objects.create(
            party_a=self.foreign_user,
            party_b=self.user,
            session=self.session,
            amount=settings.SESSION_STAKE,
            status=DuoSessionStatuses.PAIRED.value,
            winner=self.user,
        )
        self.duo_session.created_at = two_hours_ago
        self.duo_session.save()

        self.refunded_duo_session = DuoSession.objects.create(
            party_a=self.user,
            session=self.session,
            amount=settings.SESSION_STAKE,
            status=DuoSessionStatuses.REFUNDED.value,
        )

    def test_have_been_paired_recently_true(self):
        # Test for a recent session (should return True)
        self.assertTrue(
            self.pair_users.have_been_paired_recently(self.user, self.foreign_user)
        )

    def test_have_been_paired_recently_false(self):
        # Test for refunded session (should return False)
        self.duo_session.delete()
        self.assertFalse(
            self.pair_users.have_been_paired_recently(self.user, self.foreign_user)
        )

    def test_have_never_been_paired(self):
        # Test for users who have never been paired (should return False)
        self.assertFalse(
            self.pair_users.have_been_paired_recently(self.user, self.staff_user)
        )


class TestPairInstancesTestCase(BaseQuizTestCase):
    def setUp(self) -> None:
        """Set up the test environment with mock data."""
        super().setUp()
        self.pair_users = PairingService

        # Create mock instances of Result
        self.result1 = Result.objects.create(
            user=self.user,
            score=80,
            session=self.session,
            exits_at=datetime.now() + timedelta(minutes=3),
            total_answered=0,
            expires_at=datetime.now(),
        )
        self.result2 = Result.objects.create(
            score=75,
            user=self.foreign_user,
            session=self.session,
            exits_at=datetime.now() + timedelta(minutes=15),
            total_answered=3,
            expires_at=datetime.now(),
        )
        self.result3 = Result.objects.create(
            user=self.user,
            score=85,
            session=self.session,
            exits_at=datetime.now() + timedelta(minutes=-10),  # Past exit time
            total_answered=0,
            expires_at=datetime.now(),
        )
        self.result4 = Result.objects.create(
            user=self.foreign_user,
            score=90,
            session=self.session,
            exits_at=datetime.now() + timedelta(minutes=5),  # Near exit time
            total_answered=3,
            expires_at=datetime.now(),
        )

        # Mock the methods used inside pair_instances
        self.pair_users.is_partial_refund = MagicMock()  # type: ignore
        self.pair_users.is_full_refund = MagicMock()  # type: ignore
        self.pair_users.create_duo_session = MagicMock()  # type: ignore

    def tearDown(self) -> None:
        """Run after each test."""
        Result.objects.all().delete()

    def test_pair_instances_with_partial_refund(self) -> None:
        """Test that an instance with no questions answered results in a partial refund."""
        self.pair_users.is_partial_refund.return_value = True  # type: ignore
        self.pair_users.is_full_refund.return_value = False  # type: ignore
        self.pair_users.to_exclude = []
        self.pair_users.pair_instances(
            queue_ordered_by_exits_at=Result.objects.all().order_by("exits_at"),
            queue_ordered_by_score=Result.objects.all().order_by("score"),
        )

        self.pair_users.create_duo_session.assert_any_call(  # type: ignore
            party_a=self.result1.user,
            party_b=None,
            session=self.result1.session,
            duo_session_status=DuoSessionStatuses.PARTIALLY_REFUNDED.value,
            winner=None,
        )

        self.result1.refresh_from_db()
        self.assertFalse(self.result1.is_active)

    def test_pair_instances_with_full_refund(self) -> None:
        """Assert result instance with some questions answered receives a full refund."""
        self.pair_users.is_partial_refund.return_value = False  # type: ignore
        self.pair_users.is_full_refund.return_value = True  # type: ignore
        self.pair_users.to_exclude = []

        self.pair_users.pair_instances(
            queue_ordered_by_exits_at=Result.objects.all().order_by("exits_at"),
            queue_ordered_by_score=Result.objects.all().order_by("score"),
        )

        self.pair_users.create_duo_session.assert_any_call(  # type: ignore
            party_a=self.result4.user,
            party_b=None,
            session=self.result4.session,
            duo_session_status=DuoSessionStatuses.REFUNDED.value,
            winner=None,
        )

        self.result4.refresh_from_db()
        self.assertFalse(self.result4.is_active)

    def test_pair_instances_and_get_winner(self) -> None:
        """Assert paired duo session is created when an instance has a valid close instance."""
        self.pair_users.is_partial_refund.return_value = False  # type: ignore
        self.pair_users.is_full_refund.return_value = False  # type: ignore

        self.pair_users.find_closest_instance = MagicMock()  # type: ignore
        self.pair_users.find_closest_instance.return_value = self.result4

        self.pair_users.pair_instances(
            queue_ordered_by_exits_at=Result.objects.all().order_by("exits_at"),
            queue_ordered_by_score=Result.objects.all().order_by("score"),
        )

        self.pair_users.create_duo_session.assert_any_call(  # type: ignore
            party_a=self.result1.user,
            party_b=self.result4.user,
            session=self.result1.session,
            duo_session_status=DuoSessionStatuses.PAIRED.value,
            winner=self.result4.user,
        )

    def test_get_winner_party_a_wins(self):
        winner = self.pair_users.get_winner(self.result1, self.result2)
        self.assertEqual(winner, self.result1)

    def test_get_winner_party_b_wins(self):
        winner = self.pair_users.get_winner(self.result1, self.result4)
        self.assertEqual(winner, self.result4)


class DeactivateInstancesTestCase(BaseQuizTestCase):
    def setUp(self):
        """Set up the test environment with mock data."""
        super().setUp()
        # Create some Result instances
        self.result1 = Result.objects.create(
            is_active=True,
            user=self.user,
            session=self.session,
            expires_at=datetime.now(),
        )
        self.result2 = Result.objects.create(
            is_active=True,
            user=self.user,
            session=self.session,
            expires_at=datetime.now(),
        )

        # Instantiate the service that contains deactivate_instances
        self.pairing_service = PairingService

    def test_deactivate_instances(self) -> None:
        """Test that deactivate_instances sets is_active to False for the specified instances."""
        # Call the deactivate_instances method
        self.pairing_service.deactivate_instances([self.result1])

        # Refresh the instances from the database
        self.result1.refresh_from_db()
        self.result2.refresh_from_db()

        # Assert that the is_active field has been updated correctly
        self.assertFalse(self.result1.is_active)
        self.assertTrue(
            self.result2.is_active
        )  # Should remain True since it was not deactivated

    def test_deactivate_instances_empty_list(self) -> None:
        """Test that deactivate_instances does nothing when an empty list is passed."""
        # Call the deactivate_instances method with an empty list
        self.pairing_service.deactivate_instances([])

        # Refresh the instances from the database
        self.result1.refresh_from_db()
        self.result2.refresh_from_db()

        # Assert that the is_active field remains unchanged
        self.assertTrue(self.result1.is_active)
        self.assertTrue(self.result2.is_active)

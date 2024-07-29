from datetime import datetime, timedelta
from unittest.mock import MagicMock

from django.conf import settings

from commons.constants import SessionCategories
from commons.tests.base_tests import BaseQuizTestCase
from quiz.models import Result
from quiz.user_pairing import PairingService
from user_sessions.constants import SESSION_BUFFER_TIME
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
        results = MagicMock()
        results.values_list.return_value = [
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            100,
        ]  # Right skewed
        skewness = self.pair_users.calculate_skewness(results)
        self.assertGreater(skewness, 0)  # Expect a positive skew

    def test_calculate_skewness_negative(self) -> None:
        results = MagicMock()
        results.values_list.return_value = [
            100,
            90,
            80,
            70,
            60,
            50,
            40,
            30,
            20,
            1,
        ]  # Left skewed
        skewness = self.pair_users.calculate_skewness(results)
        self.assertLess(skewness, 0)  # Expect a negative skew

    def test_calculate_skewness_no_skew(self) -> None:
        results = MagicMock()
        results.values_list.return_value = [
            50,
            51,
            49,
            50,
            50,
            51,
            49,
            50,
            50,
            50,
        ]  # No skew
        skewness = self.pair_users.calculate_skewness(results)
        self.assertAlmostEqual(skewness, 0, places=1)  # Expect skewness close to zero

    def test_calculate_skewness_uniform(self) -> None:
        results = MagicMock()
        results.values_list.return_value = list(range(1, 101))  # Uniform distribution
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

from datetime import datetime
from unittest.mock import patch

from django.contrib.auth import get_user_model

from commons.constants import SessionCategories
from commons.tests.base_tests import BaseUserAPITestCase
from quiz.models import Result
from user_sessions.models import Session
from user_sessions.utils import (
    get_available_session,
    query_available_active_sessions,
    query_sessions_not_played_by_user_in_category,
)

User = get_user_model()


class QueryAvailableActiveSessionsTests(BaseUserAPITestCase):
    def setUp(self) -> None:
        # Create test users
        self.user = self.create_user()
        self.foreign_user = self.create_foreign_user()

        self.bible_category = SessionCategories.BIBLE.value
        self.football_category = SessionCategories.FOOTBALL.value

        # Create test sessions
        self.session1 = Session.objects.create(
            category=self.bible_category, _questions="Q1,Q2"
        )
        self.session2 = Session.objects.create(
            category=self.bible_category, _questions="Q3,Q4"
        )
        self.session3 = Session.objects.create(
            category=self.football_category, _questions="Q5,Q6"
        )
        self.session4 = Session.objects.create(
            category=self.bible_category, _questions="Q7,Q8"
        )

        # Create test results
        Result.objects.create(
            user=self.user,
            session=self.session1,
            is_active=True,
            expires_at=datetime.now(),
        )
        Result.objects.create(
            user=self.user,
            session=self.session3,
            is_active=True,
            expires_at=datetime.now(),
        )
        Result.objects.create(
            user=self.foreign_user,
            session=self.session2,
            is_active=True,
            expires_at=datetime.now(),
        )

    def test_user_has_available_active_sessions(self) -> None:
        """Assert only 1 active session in BIBLE category available for user"""
        available_sessions = query_available_active_sessions(
            user=self.user, category=self.bible_category
        )
        expected_sessions = [
            self.session2.id
        ]  # Sessions not played by user in BIBLE category
        self.assertListEqual(available_sessions, expected_sessions)

    def test_foreign_user_has_available_active_sessions(self) -> None:
        """Assert only 1 active session in BIBLE category available for foreing user"""
        available_sessions = query_available_active_sessions(
            user=self.foreign_user, category=self.bible_category
        )
        expected_sessions = [
            self.session1.id
        ]  # Sessions not played by foreign user in BIBLE category
        self.assertListEqual(available_sessions, expected_sessions)

    def test_user_has_no_available_active_sessions(self) -> None:
        """Assert user has no active session to play"""
        Result.objects.filter(user=self.foreign_user).update(is_active=False)
        available_sessions = query_available_active_sessions(
            user=self.user, category=self.bible_category
        )
        self.assertListEqual(available_sessions, [])

    def test_foreign_user_has_no_available_active_sessions(self) -> None:
        """Assert user has no active session to play in a different category"""
        Result.objects.filter(user=self.user).update(
            session=self.session1
        )  # Update all other sessions to BIBLE category
        available_sessions = query_available_active_sessions(
            user=self.foreign_user, category=self.football_category
        )
        self.assertListEqual(available_sessions, [])


class QuerySessionsTestCase(BaseUserAPITestCase):
    def setUp(self) -> None:
        self.user = self.create_user()
        self.foreign_user = self.create_foreign_user()

        self.category = SessionCategories.BIBLE.value

        # Create sessions in the specified category
        self.session1 = Session.objects.create(
            category=self.category, _questions="Question 1, Question 2"
        )
        self.session2 = Session.objects.create(
            category=self.category, _questions="Question 3, Question 4"
        )
        self.session3 = Session.objects.create(
            category=self.category, _questions="Question 5, Question 6"
        )

        # Create a session in a different category
        self.session_other_category = Session.objects.create(
            category=SessionCategories.FOOTBALL.value,
            _questions="Question 7, Question 8",
        )

        # Create a result for the user for one of the sessions in the specified category
        Result.objects.create(
            user=self.user, session=self.session1, expires_at=datetime.now()
        )

    def test_query_sessions_not_played_by_user_in_category(self) -> None:
        # Get the list of session IDs that the user has not played in the specified category
        result = query_sessions_not_played_by_user_in_category(
            user=self.user, category=self.category
        )

        # Check that the correct sessions are returned
        self.assertIn(self.session2.id, result)
        self.assertIn(self.session3.id, result)

        # Check that the session that the user has played is not in the result
        self.assertNotIn(self.session1.id, result)

        # Check that the session in a different category is not in the result
        self.assertNotIn(self.session_other_category.id, result)

    def test_query_sessions_with_no_results(self) -> None:
        # Get the list of session IDs that the new user has not played in the specified category
        result = query_sessions_not_played_by_user_in_category(
            user=self.foreign_user, category=self.category
        )

        # Check that all sessions in the specified category are returned
        self.assertIn(self.session1.id, result)
        self.assertIn(self.session2.id, result)
        self.assertIn(self.session3.id, result)

        # Check that the session in a different category is not in the result
        self.assertNotIn(self.session_other_category.id, result)

    def test_query_sessions_with_all_played(self) -> None:
        # Create results for the user for all sessions in the specified category
        Result.objects.create(
            user=self.user, session=self.session2, expires_at=datetime.now()
        )
        Result.objects.create(
            user=self.user, session=self.session3, expires_at=datetime.now()
        )

        # Get the list of session IDs that the user has not played in the specified category
        result = query_sessions_not_played_by_user_in_category(
            user=self.user, category=self.category
        )

        # Check that no sessions are returned
        self.assertNotIn(self.session1.id, result)
        self.assertNotIn(self.session2.id, result)
        self.assertNotIn(self.session3.id, result)


class GetAvailableSessionTestCase(BaseUserAPITestCase):
    def setUp(self):
        self.user = self.create_user()
        self.category = SessionCategories.BIBLE.value

    @patch("user_sessions.utils.query_available_active_sessions")
    @patch("user_sessions.utils.query_sessions_not_played_by_user_in_category")
    def test_only_active_sessions_in_results_are_returned(
        self, mock_query_sessions_not_played, mock_query_available_active
    ) -> None:
        # Mock query_available_active_sessions to return a non-empty list
        mock_query_available_active.return_value = [1, 2, 3]

        # Mock query_sessions_not_played_by_user_in_category to return an empty list
        mock_query_sessions_not_played.return_value = []

        # Call the function
        session_id = get_available_session(user=self.user, category=self.category)

        # Check that the session_id is one of the available active sessions
        self.assertIn(session_id, [1, 2, 3])

        # Ensure query_sessions_not_played_by_user_in_category is not called
        mock_query_sessions_not_played.assert_not_called()

    @patch("user_sessions.utils.query_available_active_sessions")
    @patch("user_sessions.utils.query_sessions_not_played_by_user_in_category")
    def test_only_ids_in_session_model_are_returned(
        self, mock_query_sessions_not_played, mock_query_available_active
    ) -> None:
        # Mock query_available_active_sessions to return an empty list
        mock_query_available_active.return_value = []

        # Mock query_sessions_not_played_by_user_in_category to return a non-empty list
        mock_query_sessions_not_played.return_value = [4, 5, 6]

        # Call the function
        session_id = get_available_session(user=self.user, category=self.category)

        # Check that the session_id is one of the sessions not played by the user
        self.assertIn(session_id, [4, 5, 6])

    @patch("user_sessions.utils.query_available_active_sessions")
    @patch("user_sessions.utils.query_sessions_not_played_by_user_in_category")
    def test_no_session_ids_are_returned(
        self, mock_query_sessions_not_played, mock_query_available_active
    ) -> None:
        # Mock query_available_active_sessions to return an empty list
        mock_query_available_active.return_value = []

        # Mock query_sessions_not_played_by_user_in_category to return an empty list
        mock_query_sessions_not_played.return_value = []

        # Call the function
        session_id = get_available_session(user=self.user, category=self.category)

        # Check that the session_id is None
        self.assertIsNone(session_id)

    @patch("user_sessions.utils.query_available_active_sessions")
    @patch("user_sessions.utils.query_sessions_not_played_by_user_in_category")
    def test_when_both_non_empty_results_are_prioritized(
        self, mock_query_sessions_not_played, mock_query_available_active
    ) -> None:
        # Mock query_available_active_sessions to return a non-empty list
        mock_query_available_active.return_value = [7, 8, 9]

        # Mock query_sessions_not_played_by_user_in_category to return a non-empty list
        mock_query_sessions_not_played.return_value = [10, 11, 12]

        # Call the function
        session_id = get_available_session(user=self.user, category=self.category)

        # Check that the session_id is one of the available active sessions
        self.assertIn(session_id, [7, 8, 9])

        # Ensure query_sessions_not_played_by_user_in_category is not called
        mock_query_sessions_not_played.assert_not_called()

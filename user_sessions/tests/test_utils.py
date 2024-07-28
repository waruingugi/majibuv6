from datetime import datetime, timedelta
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

from commons.constants import SessionCategories
from commons.tests.base_tests import BaseUserAPITestCase
from quiz.models import Answer, Choice, Question, Result, UserAnswer
from user_sessions.constants import SESSION_BUFFER_TIME
from user_sessions.models import Session
from user_sessions.utils import (
    CalculateUserScore,
    compose_quiz,
    get_available_session,
    query_available_active_sessions,
    query_sessions_not_played_by_user_in_category,
)

User = get_user_model()


class QueryAvailableActiveSessionsTests(BaseUserAPITestCase):
    def setUp(self) -> None:
        # Create test users
        self.user = self.create_user()
        self.foreign_user = User.objects.create_user(
            phone_number="+254713476781", password="password456", username="testuser2"
        )
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
        self.foreign_user = User.objects.create_user(
            phone_number="+254713476781", password="password456", username="testuser2"
        )
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


class ComposeQuizTestCase(TestCase):
    def setUp(self) -> None:
        self.category = SessionCategories.FOOTBALL.value
        self.question1 = Question.objects.create(
            category=self.category, question_text="What is 2+2?"
        )
        self.question2 = Question.objects.create(
            category=self.category, question_text="What is the capital of France?"
        )
        self.session = Session.objects.create(
            category=self.category,
            _questions=f"{self.question1.id}, {self.question2.id}",
        )

        Choice.objects.create(question=self.question1, choice_text="4")
        Choice.objects.create(question=self.question1, choice_text="22")
        Choice.objects.create(question=self.question2, choice_text="Paris")
        Choice.objects.create(question=self.question2, choice_text="London")

    def test_compose_quiz_structure(self) -> None:
        result = compose_quiz(session_id=str(self.session.id))
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

        question = result[0]
        self.assertIn("id", question)
        self.assertIn("question_text", question)
        self.assertIn("choices", question)

        choice = question["choices"][0]
        self.assertIn("id", choice)
        self.assertIn("question_id", choice)
        self.assertIn("choice_text", choice)

    def test_compose_quiz_data(self) -> None:
        result = compose_quiz(session_id=str(self.session.id))

        self.assertEqual(len(result), 2)

        question1 = result[1]
        self.assertEqual(question1["question_text"], "What is 2+2?")
        self.assertEqual(len(question1["choices"]), 2)

        question2 = result[0]
        self.assertEqual(question2["question_text"], "What is the capital of France?")
        self.assertEqual(len(question2["choices"]), 2)


class CalculateScoreTestCase(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(
            username="testuser", phone_number="+254708231101"
        )
        self.category = SessionCategories.BIBLE.value

        self.category = SessionCategories.FOOTBALL.value
        self.question1 = Question.objects.create(
            category=self.category, question_text="What is 2+2?"
        )
        self.question2 = Question.objects.create(
            category=self.category, question_text="What is the capital of France?"
        )
        self.session = Session.objects.create(
            category=self.category,
            _questions=f"{self.question1.id}, {self.question2.id}",
        )

        self.choice1 = Choice.objects.create(question=self.question1, choice_text="4")
        Choice.objects.create(question=self.question1, choice_text="22")
        Choice.objects.create(question=self.question2, choice_text="Paris")
        Choice.objects.create(question=self.question2, choice_text="London")

        self.result = Result.objects.create(
            user=self.user,
            expires_at=datetime.now()
            + timedelta(seconds=(SESSION_BUFFER_TIME + settings.SESSION_DURATION)),
            session=self.session,
        )
        self.choices = [
            {"question_id": self.question1.id, "choice": self.choice1.choice_text},
        ]
        Answer.objects.create(question=self.question1, choice=self.choice1)

    @patch("user_sessions.views.sessions.datetime")
    def test_session_not_submitted_in_time_does_not_update_result(
        self, mock_datetime
    ) -> None:
        mock_datetime.now.return_value = self.result.expires_at + timedelta(
            seconds=SESSION_BUFFER_TIME + 1
        )
        initial_total = self.result.total
        initial_score = self.result.score
        CalculateUserScore.calculate_score(
            choices=[], result_id=str(self.result.id), user=self.user
        )
        self.assertEqual(self.result.total, initial_total)
        self.assertEqual(self.result.score, initial_score)
        self.assertEqual(self.result.total_answered, 0)

    def test_create_user_answers_creates_model_instances(self) -> None:
        CalculateUserScore.calculate_score(
            choices=self.choices, result_id=str(self.result.id), user=self.user
        )
        user_answers = UserAnswer.objects.filter(user=self.user, session=self.session)
        self.result.refresh_from_db()

        total_score = self.result.score or 0.0
        total_answered: int = self.result.total_answered or 0
        total_correct_answers = CalculateUserScore.get_total_correct_questions(
            choices=self.choices
        )

        self.assertTrue(user_answers.exists())
        self.assertGreater(
            total_answered, 0, "Answered questions should be more than 0"
        )
        self.assertEqual(1, total_correct_answers)
        self.assertGreater(
            total_score,
            settings.MODERATED_LOWEST_SCORE,
            "Score can not be lower than moderated score.",
        )

    def test_calculate_total_answered_score_returns_correct_value(self) -> None:
        total_answered_score = CalculateUserScore.calculate_total_answered_score(
            settings.QUESTIONS_IN_SESSION
        )

        self.assertEqual(total_answered_score, settings.SESSION_TOTAL_ANSWERED_WEIGHT)

    def test_calculate_correct_answered_score_returns_correct_value(self) -> None:
        total_correct_score = CalculateUserScore.calculate_correct_answered_score(
            settings.QUESTIONS_IN_SESSION
        )
        assert total_correct_score == settings.SESSION_CORRECT_ANSWERED_WEIGHT

    def test_calculate_final_score_returns_correct_value(self) -> None:
        final_score = CalculateUserScore.calculate_final_score(
            settings.SESSION_TOTAL_ANSWERED_WEIGHT,
            settings.SESSION_CORRECT_ANSWERED_WEIGHT,
        )

        self.assertEqual(
            final_score,
            (
                settings.SESSION_TOTAL_ANSWERED_WEIGHT
                + settings.SESSION_CORRECT_ANSWERED_WEIGHT
            )
            * 100,
        )

    def test_moderate_score_returns_correct_value(self) -> None:
        zero_moderated_score = CalculateUserScore.moderate_score(0)
        fifty_moderated_score = CalculateUserScore.moderate_score(50)
        hundred_moderated_score = CalculateUserScore.moderate_score(100)

        self.assertEqual(zero_moderated_score, settings.MODERATED_LOWEST_SCORE)
        self.assertEqual(fifty_moderated_score, 77.5)
        self.assertEqual(hundred_moderated_score, settings.MODERATED_HIGHEST_SCORE)

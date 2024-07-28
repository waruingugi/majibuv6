from datetime import datetime, timedelta
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

from commons.constants import SessionCategories
from quiz.models import Answer, Choice, Question, Result, UserAnswer
from quiz.utils import CalculateUserScore, compose_quiz
from user_sessions.constants import SESSION_BUFFER_TIME
from user_sessions.models import Session

User = get_user_model()


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
            {"question_id": self.question2.id, "choice": ""},
        ]
        Answer.objects.create(question=self.question1, choice=self.choice1)

    @patch("quiz.utils.datetime")
    def test_session_not_submitted_in_time_does_not_update_result(
        self, mock_datetime
    ) -> None:
        mock_datetime.now.return_value = self.result.expires_at + timedelta(
            seconds=SESSION_BUFFER_TIME + 1
        )
        initial_total = self.result.total
        initial_score = self.result.score
        CalculateUserScore.calculate_score(
            choices=self.choices, result_id=str(self.result.id), user=self.user
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

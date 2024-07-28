import random
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Subquery
from django.shortcuts import get_object_or_404

from commons.raw_logger import logger
from quiz.models import Answer, Choice, Question, Result, UserAnswer
from user_sessions.constants import SESSION_BUFFER_TIME
from user_sessions.models import Session

User = get_user_model()


def query_available_active_sessions(*, user, category) -> list:
    """
    Query Results model and get all results that are not paired.
    These results should be active(i.e not paired), same as category specified and
    not played by the user.
    """
    logger.info(
        f"Querying available active {category} sessions for {user.phone_number}."
    )
    # Get the list of session IDs that user has played in the specified category
    played_sessions = Result.objects.filter(
        user=user, session__category=category
    ).values_list("session_id", flat=True)

    # Get the list of active session IDs that user has not played in the specified category
    available_sessions = (
        Result.objects.filter(is_active=True, session__category=category)
        .exclude(session_id__in=played_sessions)
        .values_list("session_id", flat=True)
    )

    # Convert to a list if needed
    available_session_ids = list(available_sessions)

    return available_session_ids


def query_sessions_not_played_by_user_in_category(*, user, category) -> list:
    """Query Sessions model by category for an id the user has not played."""
    # Get the list of session IDs that the user has played in the specified category
    logger.info(f"Querying {category} sessions not played by {user.phone_number}.")
    played_sessions = Result.objects.filter(
        user=user, session__category=category
    ).values("session_id")

    # Get the list of session IDs in the specified category that the user has not played
    available_sessions = (
        Session.objects.filter(category=category)
        .exclude(id__in=Subquery(played_sessions))
        .values_list("id", flat=True)
    )

    # Convert to a list if needed
    available_session_ids = list(available_sessions)

    return available_session_ids


def get_available_session(*, user, category) -> str | None:
    logger.info(f"Get available {category} session id for {user.phone_number}.")
    available_session_ids = query_available_active_sessions(
        user=user, category=category
    )
    if not available_session_ids:
        available_session_ids = query_sessions_not_played_by_user_in_category(
            user=user, category=category
        )

    return random.choice(available_session_ids) if available_session_ids else None


def compose_quiz(session_id: str) -> list:
    """Compile questions and choices to create a quiz.
    Returned object should follow QuizObjectSerializer format"""
    logger.info("Composing session quiz...")
    quiz = []

    session = Session.objects.get(id=session_id)
    questions = Question.objects.filter(id__in=session.questions)
    choices = Choice.objects.filter(question__in=questions)

    for question in questions:
        quiz_object = {
            "id": str(question.id),
            "question_text": question.question_text,
            "choices": [
                {
                    "id": str(choice.id),
                    "question_id": str(choice.question_id),
                    "choice_text": choice.choice_text,
                }
                for choice in choices
                if choice.question_id == question.id
            ],
        }
        quiz.append(quiz_object)

    return quiz


class CalculateScore:
    def __init__(self) -> None:
        pass

    def calculate_score(self, *, choices: list, result_id: str, user) -> None:
        """Compile all functions that work together to provide the final user score"""
        logger.info(
            f"Calling CalculateScore class for Result ID: {result_id} by user_id: {user.phone_number}"
        )

        try:
            result = get_object_or_404(Result, id=result_id)

            self.user = user
            self.result = result

            if self.session_is_submitted_in_time():
                total_answered = self.create_user_answers(choices)
                total_correct = self.get_total_correct_questions(choices)

                total_answered_score = self.calculate_total_answered_score(
                    total_answered
                )
                total_correct_answered_score = self.calculate_correct_answered_score(
                    total_correct
                )

                final_score = self.calculate_final_score(
                    total_answered_score, total_correct_answered_score
                )
                moderated_score = self.moderate_score(final_score)

                result.total_correct = total_correct
                result.total_answered = total_answered
                result.total = final_score
                result.score = moderated_score
                result.save()

        except Exception as e:
            logger.error(f"CalculateScore class failed with response: {e}")
            raise e

    def session_is_submitted_in_time(self) -> bool:
        """Assert the session answers were submitted in time"""
        logger.info(f"Assert result_id: {self.result.id} was submitted in time")
        buffer_time = self.result.expires_at + timedelta(seconds=SESSION_BUFFER_TIME)
        if datetime.now() > buffer_time:
            logger.info(f"Result ID: {self.result.id} was NOT submitted in time")
            return False
        return True

    def create_user_answers(self, choices) -> int:
        """Save user answers to UserAnswer model"""
        logger.info(f"Saving answers for Result ID: {self.result.id} to db")
        total_answered = 0
        for item in choices:
            question_obj = Question.objects.get(id=item["question_id"])
            choice_obj = get_object_or_404(
                Choice, question=question_obj, choice_text=item["choice"]
            )
            UserAnswer.objects.create(
                user=self.user,
                question=question_obj,
                choice=choice_obj,
                session=self.result.session,
            )
            total_answered += 1
        return total_answered

    def get_total_correct_questions(self, choices) -> int:
        """Calculate total questions user got correct"""
        logger.info("Calculating total correct questions...")
        total_correct = 0

        for item in choices:
            question_obj = Question.objects.get(id=item["question_id"])
            choice_obj = get_object_or_404(
                Choice, question=question_obj, choice_text=item["choice"]
            )
            answer_obj = Answer.objects.get(question=question_obj)

            if answer_obj.choice == choice_obj:
                total_correct += 1

        return total_correct

    def calculate_total_answered_score(self, total_answered: int) -> float:
        """Calculate total answered score"""
        logger.info("Calculating total answered questions...")
        return settings.SESSION_TOTAL_ANSWERED_WEIGHT * (
            total_answered / settings.QUESTIONS_IN_SESSION
        )

    def calculate_correct_answered_score(self, total_correct: int) -> float:
        """Calculate total correct score"""
        logger.info("Calculating answered score...")
        return settings.SESSION_CORRECT_ANSWERED_WEIGHT * (
            total_correct / settings.QUESTIONS_IN_SESSION
        )

    def calculate_final_score(
        self, total_answered_score: float, total_correct_score: float
    ) -> float:
        """Calculate final score"""
        logger.info("Calculating final score...")
        return (total_answered_score + total_correct_score) * 100

    def moderate_score(self, final_score: float) -> float:
        """
        Moderates the final score using range mapping.
        """
        logger.info("Calculating moderated score...")
        normalized_score = (final_score - 0.0) / (100.0 - 0.0)
        moderated_score = (
            normalized_score
            * (settings.MODERATED_HIGHEST_SCORE - settings.MODERATED_LOWEST_SCORE)
        ) + settings.MODERATED_LOWEST_SCORE
        return moderated_score


CalculateUserScore = CalculateScore()

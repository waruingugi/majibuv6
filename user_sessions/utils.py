import random

from django.contrib.auth import get_user_model
from django.db.models import Subquery

from quiz.models import Choice, Question, Result
from user_sessions.models import Session

User = get_user_model()


def query_available_active_sessions(*, user, category) -> list:
    """
    Query Results model and get all results that are not paired.
    These results should be active(i.e not paired), same as category specified and
    not played by the user.
    """
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

import random

from django.contrib.auth import get_user_model
from django.db.models import Q, Subquery

from commons.raw_logger import logger
from quiz.models import Answer, Result, UserAnswer
from user_sessions.models import DuoSession, Session

User = get_user_model()


def get_duo_session_details(*, user, duo_session_id) -> dict:
    """Compile results between party_a and party_b"""
    logger.info(f"Compiling duosession details for {user.phone_number}")
    duo_session = DuoSession.objects.get(
        Q(id=duo_session_id) & (Q(party_a=user) | Q(party_b=user))
    )
    data = {
        "id": str(duo_session.id),
        "category": duo_session.session.category,  # type: ignore
        "status": duo_session.status,
        "party_a": {},
        "party_b": {},
    }

    data["party_a"] = get_result_answers(
        user=duo_session.party_a, session=duo_session.session
    )
    if duo_session.party_b:
        data["party_b"] = get_result_answers(
            user=duo_session.party_b, session=duo_session.session
        )
    return data


def mask_phone_number(phone_number: str) -> str:
    return f"{phone_number[:6]}****{phone_number[-3:]}"


def get_result_answers(*, user, session) -> dict:
    logger.info(f"Getting result answers for {user.phone_number}")
    result = Result.objects.get(user=user, session=session)
    data = {
        "username": user.username,
        "phone_number": mask_phone_number(str(user.phone_number)),
        "score": float(result.score),  # type: ignore
        "total_answered": result.total_answered,
        "total_correct": result.total_correct,
        "questions": [],
    }

    user_answers = UserAnswer.objects.filter(user=user, session=session)
    for answer in user_answers:
        correct_choice = Answer.objects.get(question=answer.question)

        data["questions"].append(
            {
                "question": answer.question.question_text,
                "choice": answer.choice.choice_text,
                "is_correct": (
                    True if correct_choice.choice.id == answer.choice.id else False
                ),
            }
        )

    return data


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

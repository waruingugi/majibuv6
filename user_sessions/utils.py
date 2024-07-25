from django.contrib.auth import get_user_model

from quiz.models import Result

User = get_user_model()


def query_available_active_sessions(*, user, category) -> list:
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

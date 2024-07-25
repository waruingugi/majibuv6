from django.contrib.auth import get_user_model

from quiz.models import Result

User = get_user_model()


def query_available_active_sessions(user) -> list:
    # Get the list of session IDs that user has played
    played_sessions = Result.objects.filter(user=user).values_list(
        "session_id", flat=True
    )

    # Get the list of active session IDs that user has not played
    available_sessions = (
        Result.objects.filter(is_active=True)
        .exclude(session_id__in=played_sessions)
        .values_list("session_id", flat=True)
    )

    # Convert to a list if needed
    available_session_ids = list(available_sessions)

    return available_session_ids

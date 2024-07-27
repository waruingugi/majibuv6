# urls.py
from django.urls import path

from user_sessions.views.sessions import (
    AvailableSessionView,
    BusinessHoursView,
    QuizRequestView,
    QuizSubmissionView,
    SessionDetailsView,
)

app_name = "sessions"


urlpatterns = [
    path("business-hours/", BusinessHoursView.as_view(), name="business-hours"),
    path("details/", SessionDetailsView.as_view(), name="details"),
    path(
        "avialable-session/", AvailableSessionView.as_view(), name="available-session"
    ),
    path("request/", QuizRequestView.as_view(), name="request-session"),
    path("submit/", QuizSubmissionView.as_view(), name="submit-session"),
]

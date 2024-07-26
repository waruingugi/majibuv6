# urls.py
from django.urls import path

from user_sessions.views.sessions import (
    AvailableSessionView,
    BusinessHoursView,
    QuizView,
    SessionDetailsView,
)

app_name = "sessions"


urlpatterns = [
    path("business-hours/", BusinessHoursView.as_view(), name="business-hours"),
    path("details/", SessionDetailsView.as_view(), name="details"),
    path(
        "avialable-session/", AvailableSessionView.as_view(), name="available-session"
    ),
    path("quiz/", QuizView.as_view(), name="quiz"),
]

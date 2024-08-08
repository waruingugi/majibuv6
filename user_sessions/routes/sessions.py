# urls.py
from django.urls import path

from user_sessions.views.sessions import (
    AvailableSessionView,
    BusinessHoursView,
    DuoSessionDetailsView,
    DuoSessionListView,
    MobileAdView,
    SessionDetailsView,
)

app_name = "sessions"


urlpatterns = [
    path("business-hours/", BusinessHoursView.as_view(), name="business-hours"),
    path("details/", SessionDetailsView.as_view(), name="details"),
    path(
        "avialable-session/", AvailableSessionView.as_view(), name="available-session"
    ),
    path("duo-session/", DuoSessionListView.as_view(), name="duo-session-list"),
    path(
        "duo-session/<str:id>/detail/",
        DuoSessionDetailsView.as_view(),
        name="duo-session-details",
    ),
    path("mobile-ad/", MobileAdView.as_view(), name="mobile-ad"),
]

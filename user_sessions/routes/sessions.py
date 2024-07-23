# urls.py
from django.urls import path

from user_sessions.views.sessions import BusinessHoursView, SessionDetailsView

app_name = "sessions"


urlpatterns = [
    path("business-hours/", BusinessHoursView.as_view(), name="business-hours"),
    path("details/", SessionDetailsView.as_view(), name="details"),
]

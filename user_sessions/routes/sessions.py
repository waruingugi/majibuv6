# urls.py
from django.urls import path

from user_sessions.views.sessions import BusinessHoursView

app_name = "sessions"

urlpatterns = [
    path("business-hours/", BusinessHoursView.as_view(), name="business-hours"),
]

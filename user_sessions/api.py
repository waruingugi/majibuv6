from django.urls import include, path

from user_sessions.routes import sessions

urlpatterns = [
    path("sessions/", include((sessions.urlpatterns, "sessions"))),
]

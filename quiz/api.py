from django.urls import include, path

from quiz.routes import quiz

urlpatterns = [
    path("sessions/", include((quiz.urlpatterns, "quiz"))),
]

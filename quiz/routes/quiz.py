# urls.py
from django.urls import path

from quiz.views.quiz import QuizRequestView, QuizSubmissionView, ResultRetrieveView

app_name = "quiz"


urlpatterns = [
    path("request/", QuizRequestView.as_view(), name="request-quiz"),
    path("submit/", QuizSubmissionView.as_view(), name="submit-quiz"),
    path("result/<str:id>/", ResultRetrieveView.as_view(), name="result-retrieve"),
]

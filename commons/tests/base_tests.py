from datetime import datetime

from django.test import TestCase
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from commons.constants import SessionCategories
from quiz.models import Answers, Choices, Questions, Results, UserAnswers
from user_sessions.models import Sessions
from users.models import User


class BaseUserAPITestCase(APITestCase):
    phone_number = "+254712345678"
    password = "testpassword"
    username = "testuser"
    staff_username = "admin"
    staff_phone_number = "0701234567"
    staff_password = "Adminpassword123"

    def create_user(self) -> User:
        self.user = User.objects.create_user(
            username=self.username,
            password=self.password,
            phone_number=self.phone_number,
        )
        return self.user

    def create_staff_user(self) -> User:
        self.staff_user = User.objects.create_user(
            phone_number=self.staff_phone_number,
            username=self.staff_username,
            password=self.staff_password,
            is_staff=True,
        )
        return self.staff_user

    def force_authenticate_user(self) -> None:
        self.client = APIClient()
        if not hasattr(self, "user"):
            self.user = self.create_user()

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def force_authenticate_staff_user(self) -> None:
        if not hasattr(self, "staff_user"):
            self.create_staff_user()

        self.client = APIClient()
        self.client.force_authenticate(user=self.staff_user)

    def create_access_token(self, user) -> str:
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)  # type: ignore


class BaseQuizTestCase(TestCase):
    def setUp(self) -> None:
        self.user = BaseUserAPITestCase().create_user()

        self.question_text = "What is the chemical symbol for water?"
        self.category = SessionCategories.FOOTBALL.value
        self.question = Questions.objects.create(
            category=self.category, question_text=self.question_text
        )

        self.choice_text = "H2O"
        self.choice = Choices.objects.create(
            question=self.question, choice_text=self.choice_text
        )
        self.answer = Answers.objects.create(question=self.question, choice=self.choice)

        self.session = Sessions.objects.create(category=self.category)
        self.user_answer = UserAnswers.objects.create(
            user=self.user,
            question=self.question,
            choice=self.choice,
            session=self.session,
        )

        self.result = Results.objects.create(
            user=self.user, session=self.session, expires_at=datetime.now()
        )

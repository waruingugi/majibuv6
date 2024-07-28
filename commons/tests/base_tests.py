from datetime import datetime

# from django.conf import settings
from django.test import TestCase
from phone_gen import PhoneNumber
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from commons.constants import SessionCategories
from quiz.models import Answer, Choice, Question, Result, UserAnswer
from user_sessions.models import Session
from users.models import User


def random_phone(country_iso_2_code: str = "KE") -> str:
    """Generate random phone number"""
    faker_phone_number = PhoneNumber(country_iso_2_code)
    return faker_phone_number.get_mobile(full=True)


def run_before(before_funcs):
    """A decorator to run a specified funs before the main one excutes."""

    def decorator(original_func):
        def wrapper(*args, **kwargs):
            for before_func in before_funcs:
                before_func(
                    *args, **kwargs
                )  # Call each "before" function with the same arguments
            return original_func(
                *args, **kwargs
            )  # Call the original function with the same arguments

        return wrapper

    return decorator


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

    def create_foreign_user(self) -> User:
        self.foreign_user = User.objects.create_user(
            phone_number="+254713476781", password="password456", username="testuser2"
        )
        return self.foreign_user

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
        self.question = Question.objects.create(
            category=self.category, question_text=self.question_text
        )

        self.choice_text = "H2O"
        self.choice = Choice.objects.create(
            question=self.question, choice_text=self.choice_text
        )
        self.answer = Answer.objects.create(question=self.question, choice=self.choice)

        self.session = Session.objects.create(category=self.category)
        self.user_answer = UserAnswer.objects.create(
            user=self.user,
            question=self.question,
            choice=self.choice,
            session=self.session,
        )

        self.result = Result.objects.create(
            user=self.user, session=self.session, expires_at=datetime.now()
        )


# class BaseSessionTestCase(TestCase):
#     def create_staff_user(self) -> None:
#         self.staff_user = User.objects.create(
#             phone_number="0701234567",
#             username="admin",
#             is_staff=True,
#         )

#     def delete_result_model_instances(self) -> None:
#         """Delete all existing rows in Results model"""
#         Result.objects.all().delete()

#     def delete_session_model_instances(self) -> None:
#         """Delete all existing rows in Sessions model"""
#         Session.objects.all().delete()

#     def delete_duo_session_model_instances(self) -> None:
#         """Delete previously existing rows in DuoSession model"""
#         DuoSession.objects.all().delete()

#     def create_user_model_instances(self) -> None:
#         """Create several user model instances"""
#         for _ in range(10):
#             User.objects.create(phone=random_phone())

#     @run_before(delete_session_model_instances)
#     def create_session_model_instances(self) -> None:
#         """Create several session model instances"""
#         for _ in range(10):
#             question_ids_str = ""
#             for _ in range(settings.QUESTIONS_IN_SESSION):
#                 question = str(uuid.uuid4) + ", "
#                 question_ids_str += question

#             Session.objects.create(
#                 category=SessionCategories.FOOTBALL.value, _questions=question_ids_str
#             )

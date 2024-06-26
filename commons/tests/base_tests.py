from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class BaseUserAPITestCase(APITestCase):
    phone_number = "+254712345678"
    password = "testpassword"
    username = "testuser"
    staff_username = "admin"
    staff_phone_number = "0701234567"
    staff_password = "Adminpassword123"

    def force_authentication_user(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            username=self.username,
            password=self.password,
            phone_number=self.phone_number,
        )
        self.client.force_authenticate(user=self.user)

    def create_staff_user(self) -> None:
        self.staff_user = User.objects.create_user(
            phone_number=self.staff_phone_number,
            username=self.staff_username,
            password=self.staff_password,
            is_staff=True,
        )
        self.staff_access_token = self.create_access_token(self.staff_user)

        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.staff_access_token)

    def create_access_token(self, user) -> str:
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)  # type: ignore

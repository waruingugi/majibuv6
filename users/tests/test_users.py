from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from users.constants import MAX_USERNAME_LEN, MIN_USERNAME_LEN
from users.models import User


class BaseUserAPITestCase(APITestCase):
    def create_staff_user(self) -> None:
        self.staff_user = User.objects.create_user(
            phone_number="0701234567",
            username="admin",
            password="Adminpassword123",
            is_staff=True,
        )
        self.staff_access_token = self.create_access_token(self.staff_user)

        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.staff_access_token)

    def create_access_token(self, user) -> str:
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)  # type: ignore


class UserCreateAPIViewTests(BaseUserAPITestCase):
    def setUp(self) -> None:
        self.create_url = reverse("users:user-create")
        self.data = {
            "phone_number": "0703245678",
            "username": "stacy",
            "password": "passwordAl123",
        }
        self.create_staff_user()

    def test_staff_user_creates_user_successfully(self) -> None:
        """Assert endpoint creates user successfully."""

        response = self.client.post(self.create_url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertIn("phone_number", response.data)
        self.assertIn("username", response.data)
        self.assertFalse(response.data["is_verified"])
        self.assertFalse(response.data["is_active"])

    def test_normal_user_fails_to_create_user(self) -> None:
        """Assert normal users do not have permission to create users."""
        normal_user = User.objects.create(
            phone_number="0778245678",
            username="normaluser",
            password="passwordAl123",
        )
        access_token = self.create_access_token(normal_user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer " + access_token)
        response = self.client.post(self.create_url, self.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertIn("phone_number", response.data)
        self.assertIn("username", response.data)
        self.assertFalse(response.data["is_verified"])
        self.assertFalse(response.data["is_active"])

    def test_view_generates_default_username(self) -> None:
        """Assert a default username is generated if the field is not defined."""
        data = {"phone_number": "0703245674", "password": "password124"}
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.data["username"])

    def test_view_fails_if_username_is_too_long(self) -> None:
        """Assert username does not exceed maximum string length."""
        username = "a" * (MAX_USERNAME_LEN + 1)
        data = {
            "phone_number": "0703245674",
            "username": username,
            "password": "password124",
        }
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_view_fails_if_username_is_too_short(self) -> None:
        """Assert username is not below minimum string length."""
        username = "a" * (MIN_USERNAME_LEN - 1)
        data = {
            "phone_number": "0703245674",
            "username": username,
            "password": "password124",
        }
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_view_fails_if_username_has_special_characters(self) -> None:
        """Assert username is not below minimum string length."""
        username = "testuser*"
        data = {
            "phone_number": "0703245674",
            "username": username,
            "password": "password124",
        }
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_view_fails_if_phone_number_field_is_missing(self) -> None:
        """Assert validation error is raised if phone number field is missing."""
        data = {
            "password": "password123",
        }
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone_number", response.data)

    def test_view_fails_if_phone_number_is_not_valid(self) -> None:
        """Assert validation error is raised if phone number is invalid."""
        data = {"phone_number": "070324", "password": "password124"}
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserRetrieveUpdateAPIViewTests(BaseUserAPITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            phone_number="+254703456781",
            password="password456",
            username="testuser1",
        )
        self.foreign_user = User.objects.create_user(
            phone_number="+254713476781", password="password456", username="testuser2"
        )
        self.detail_url = reverse("users:user-detail", kwargs={"id": self.user.id})

        self.create_staff_user()
        access_token = self.create_access_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + access_token)

    def test_user_can_not_update_read_only_fields(self) -> None:
        """Assert the phone number field can not be edited."""
        data = {
            "phone_number": "+254703456782",
            "is_staff": True,
            "is_active": False,
            "is_verified": True,
        }
        response = self.client.put(self.detail_url, data)

        self.user.refresh_from_db()
        self.assertEqual(self.user.phone_number, "+254703456781")
        self.assertFalse(response.data["is_verified"])
        self.assertFalse(response.data["is_staff"])
        self.assertTrue(response.data["is_active"])

    def test_user_can_edit_their_profile(self) -> None:
        """Assert a user can edit themselves."""
        data = {"username": "activerodent"}

        response = self.client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "activerodent")

    def test_staff_can_edit_other_users(self) -> None:
        """Assert a staff user can edit other users.."""
        data = {
            "is_active": False,
            "is_verified": False,
        }
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer " + self.staff_access_token)
        response = client.put(self.detail_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertEqual(self.user.is_active, False)

    def test_user_can_update_username_field(self) -> None:
        """Assert user can update their own username"""
        data = {"username": "foreignuser"}
        response = self.client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "foreignuser")

    def test_view_fails_to_update_if_username_exists(self) -> None:
        """Assert updating to username that exists fails."""
        prev_username = self.user.username
        User.objects.create_user(
            phone_number="+254703456785",
            password="password455",
            username="testuser5",
        )
        data = {"username": "testuser5"}
        response = self.client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, prev_username)

    def test_view_retrieves_user_data(self) -> None:
        """Assert expected fields are returned in detail view."""
        response = self.client.put(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("id", response.data)
        self.assertIn("phone_number", response.data)
        self.assertIn("username", response.data)
        self.assertIn("is_verified", response.data)
        self.assertIn("is_active", response.data)
        self.assertIn("is_staff", response.data)


class UserListAPIViewTests(BaseUserAPITestCase):
    def setUp(self) -> None:
        self.user1 = User.objects.create_user(
            phone_number="+254703456785", password="password123", username="testuser1"
        )
        self.user2 = User.objects.create_user(
            phone_number="+254703456781", password="password456", username="testuser2"
        )
        self.list_url = reverse("users:user-list")

        self.create_staff_user()

    def test_view_returns_list_of_users(self) -> None:
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_normal_user_can_not_list_users(self) -> None:
        client = APIClient()
        access_token = self.create_access_token(self.user1)
        client.credentials(HTTP_AUTHORIZATION="Bearer " + access_token)

        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from commons.constants import MAX_USERNAME_LEN, MIN_USERNAME_LEN
from users.models import User


class UserCreateTests(APITestCase):
    def setUp(self) -> None:
        self.create_url = reverse("users:user-create")

    def test_view_creates_user_successfully(self) -> None:
        """Assert endpoint creates user successfully."""
        data = {
            "phone_number": "0703245678",
            "username": "stacy",
            "password": "password123",
        }

        response = self.client.post(self.create_url, data)
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


class UserUpdateTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            phone_number="+254703456781",
            password="password456",
            username="testuser1",
        )
        self.update_url = reverse("users:user-detail", kwargs={"id": self.user.id})

    def test_user_can_not_update_phone_number_field(self) -> None:
        """Assert the phone number field can not be edited."""
        data = {"phone_number": "+254703456782"}
        response = self.client.put(self.update_url, data)
        self.assertNotIn("phone_number", response.data)

        self.user.refresh_from_db()
        self.assertEqual(self.user.phone_number, "+254703456781")

    def test_user_can_update_username_field(self) -> None:
        """Assert user can update their own username"""
        data = {"username": "testuser2"}
        response = self.client.put(self.update_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "testuser2")

    def test_view_fails_to_update_if_username_exists(self) -> None:
        """Assert updating to username that exists fails."""
        prev_username = self.user.username
        User.objects.create_user(
            phone_number="+254703456785",
            password="password455",
            username="testuser5",
        )
        data = {"username": "testuser5"}
        response = self.client.put(self.update_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, prev_username)

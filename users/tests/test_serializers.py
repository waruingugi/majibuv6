from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class UserCreateAPIViewTest(APITestCase):
    def setUp(self) -> None:
        self.create_url = reverse("users:user-create")

    def test_view_creates_user_successfully(self) -> None:
        """Assert endpoint creates user successfully."""
        data = {"phone_number": "0703245678", "password": "password123"}

        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertIn("phone_number", response.data)
        self.assertIn("username", response.data)
        self.assertFalse(response.data["is_verified"])
        self.assertFalse(response.data["is_active"])

    def test_create_view_fails_on_missing_phone_number(self) -> None:
        """Assert endpoint fails if"""
        data = {
            "password": "password123",
        }
        response = self.client.post(self.create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone_number", response.data)

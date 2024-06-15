from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class UserModelTests(TestCase):
    def setUp(self) -> None:
        """Set up test data."""
        self.test_phone_number = "+254701301401"
        self.test_password = "password123"
        self.test_username = "testuser"
        self.user = User.objects.create_user(
            phone_number=self.test_phone_number,
            password=self.test_password,
            username=self.test_username,
        )

    def test_create_user(self) -> None:
        """Assert fields created have the same value as those passed."""

        self.assertEqual(self.user.phone_number, self.test_phone_number)
        self.assertTrue(self.user.check_password(self.test_password))
        self.assertEqual(self.user.username, self.test_username)
        self.assertFalse(self.user.is_verified)
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)

    def test_phone_number_is_unique(self) -> None:
        """Assert phone number is unique for all users."""

        with self.assertRaises(Exception):
            User.objects.create_user(
                phone_number=self.test_phone_number,
                password="password456",
                username="testuser1",
            )

    def test_username_is_unique(self) -> None:
        """Assert username is unique for all users."""

        with self.assertRaises(Exception):
            User.objects.create_user(
                phone_number="+254701301405",
                password="password456",
                username=self.test_username,
            )

import json

from django.http import JsonResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from commons.constants import User
from commons.middlewares import UserIsActiveMiddleware


class UserIsActiveMiddlewareTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = UserIsActiveMiddleware(
            lambda request: JsonResponse({"detail": "Passed"}, status=200)
        )

        # Create an active and inactive user
        self.active_user = User.objects.create_user(
            phone_number="+254703457891", password="StrongPassword123", is_active=True
        )
        self.inactive_user = User.objects.create_user(
            phone_number="+254721457891", password="StrongPassword123", is_active=False
        )

        # Generate tokens for both users
        self.active_token = str(RefreshToken.for_user(self.active_user).access_token)  # type: ignore
        self.inactive_token = str(
            RefreshToken.for_user(self.inactive_user).access_token  # type: ignore
        )

    def test_active_user_is_not_logged_out(self):
        request = self.factory.get(reverse("users:user-list"))
        request.META["HTTP_AUTHORIZATIOIN"] = f"Bearer {self.active_token}"

        response = self.middleware.process_request(request)

        self.assertIsNone(response)

    def test_inactive_user_is_logged_out(self):
        request = self.factory.get(reverse("users:user-list"))
        request.META["HTTP_AUTHORIZATION"] = f"Bearer {self.inactive_token}"

        response = self.middleware.process_request(request)

        # Middleware should block the request and return a 401 response
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # type: ignore
        self.assertEqual(
            json.loads(response.content)["detail"],  # type: ignore
            "This account is inactive.",
        )

    def test_requests_with_no_token_does_not_raise_an_error(self):
        request = self.factory.get(reverse("users:user-list"))

        response = self.middleware.process_request(request)

        # No response means the middleware let the request pass through
        self.assertIsNone(response)

    def test_invalid_token_raises_error(self):
        request = self.factory.get(reverse("users:user-list"))
        request.META["HTTP_AUTHORIZATION"] = "Bearer invalidtoken"

        response = self.middleware.process_request(request)

        # Middleware should block the request and return a 401 response
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # type: ignore
        self.assertEqual(json.loads(response.content)["detail"], "Invalid token.")  # type: ignore

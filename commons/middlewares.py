import logging

from django.contrib.auth import get_user_model
from django.http.response import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from log_request_id import local
from rest_framework import status
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


User = get_user_model()


class UserIsActiveMiddleware(MiddlewareMixin):
    """Log out inactive users."""

    def process_request(self, request) -> None | JsonResponse:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

            try:
                # Decode the token
                access_token = AccessToken(token)
                user = User.objects.get(id=access_token["user_id"])

                if not user.is_active:
                    # Invalidate the token
                    try:
                        token = RefreshToken(token)
                        token.blacklist()
                    except TokenError:
                        pass

                    # Logout the user
                    return JsonResponse(
                        {"detail": "This account is inactive."},
                        status=status.HTTP_401_UNAUTHORIZED,
                    )

            except (TokenError, User.DoesNotExist):
                return JsonResponse(
                    {"detail": "Invalid token."}, status=status.HTTP_401_UNAUTHORIZED
                )

        return None


class RequestResponseLoggerMiddleware(MiddlewareMixin):
    def process_request(self, request):
        user_id = request.user.id if request.user.is_authenticated else "Anonymous"
        request_id = local.request_id
        logger.info(
            f"Request ID: {request_id} | User ID: {user_id} | Request: {request.method} {request.get_full_path()}"
        )

    def process_response(self, request, response):
        user_id = request.user.id if request.user.is_authenticated else "Anonymous"
        request_id = local.request_id
        response["Request-ID"] = request_id
        logger.info(
            f"Request ID: {request_id} | User ID: {user_id} | Response: {response.status_code}"
        )

        return response

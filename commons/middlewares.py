from django.contrib.auth import get_user_model
from django.http.response import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework import status
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

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

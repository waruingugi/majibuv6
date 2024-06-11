from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveUpdateAPIView,
)

from users.base_views import UserBaseView


class UserCreateAPIView(UserBaseView, CreateAPIView):
    """Create a user."""

    pass


class UserListAPIView(ListAPIView):
    "List users."

    pass


class UserRetrieveUpdateAPIView(UserBaseView, RetrieveUpdateAPIView):
    """Retrieve a user."""

    lookup_field = "id"


class UserDeleteAPIView(DestroyAPIView):
    """Delete a user."""

    lookup_field = "id"

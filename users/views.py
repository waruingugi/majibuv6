from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveUpdateAPIView,
)

from users.models import User
from users.serializers import (
    AdminUserUpdateSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
)


class UserCreateAPIView(CreateAPIView):
    """Create a user."""

    queryset = User.objects.all()
    serializer_class = UserCreateSerializer


class UserListAPIView(ListAPIView):
    "List users."

    pass


class UserRetrieveUpdateAPIView(RetrieveUpdateAPIView):
    """Retrieve a user."""

    lookup_field = "id"
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return AdminUserUpdateSerializer
        return UserUpdateSerializer


class UserDeleteAPIView(DestroyAPIView):
    """Delete a user."""

    lookup_field = "id"

from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveUpdateAPIView

from commons.permissions import IsStaffOrSelfPermission, IsStaffPermission
from users.models import User
from users.serializers import (
    StaffUserRetrieveUpdateSerializer,
    UserCreateSerializer,
    UserListSerializer,
    UserRetrieveUpdateSerializer,
)


class UserCreateView(CreateAPIView):
    """Create a user."""

    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [IsStaffPermission]


class UserListView(ListAPIView):
    "List users."

    queryset = User.objects.all()
    serializer_class = UserListSerializer
    permission_classes = [IsStaffPermission]


class UserRetrieveUpdateView(RetrieveUpdateAPIView):
    """Retrieve a user."""

    lookup_field = "id"
    queryset = User.objects.all()
    permission_classes = [IsStaffOrSelfPermission]

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return StaffUserRetrieveUpdateSerializer
        return UserRetrieveUpdateSerializer

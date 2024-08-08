from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import (
    CreateAPIView,
    GenericAPIView,
    ListAPIView,
    RetrieveUpdateAPIView,
)
from rest_framework.response import Response

from commons.pagination import StandardPageNumberPagination
from commons.permissions import IsStaffOrSelfPermission, IsStaffPermission
from users.models import User
from users.serializers import (
    LatestAppVersionSerializer,
    StaffUserCreateSerializer,
    StaffUserRetrieveUpdateSerializer,
    UserListSerializer,
    UserRetrieveUpdateSerializer,
)


class UserCreateView(CreateAPIView):
    """Create a user."""

    queryset = User.objects.all()
    serializer_class = StaffUserCreateSerializer
    permission_classes = [IsStaffPermission]


class UserListView(ListAPIView):
    "List users."

    queryset = User.objects.all()
    serializer_class = UserListSerializer
    permission_classes = [IsStaffPermission]
    pagination_class = StandardPageNumberPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    search_fields = ["phone_number", "username"]
    filterset_fields = ["is_active", "is_verified", "is_staff"]
    ordering_fields = ["created_at"]


class UserRetrieveUpdateView(RetrieveUpdateAPIView):
    """Retrieve a user."""

    lookup_field = "id"
    queryset = User.objects.all()
    permission_classes = [IsStaffOrSelfPermission]

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return StaffUserRetrieveUpdateSerializer
        return UserRetrieveUpdateSerializer


class LatestAppVersionView(GenericAPIView):
    """Returns the latest app version recognized by the API.
    Users can not use app until they update to latest app version"""

    serializer_class = LatestAppVersionSerializer

    def get(self, request, *args, **kwargs):
        data = {"app_version": settings.LATEST_APP_VERSION}
        serializer = LatestAppVersionSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

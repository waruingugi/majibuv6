from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.response import Response

from notifications.models import Notification
from notifications.serializers import (
    MarkNotificationsReadSerializer,
    NotificationListSerializer,
    UnreadNotificationCountSerializer,
)


class NotificationListView(ListAPIView):
    "List Notifications"

    queryset = Notification.objects.all()
    serializer_class = NotificationListSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    search_fields = ["receiving_party", "user__phone_number", "user__id"]
    filterset_fields = ["type", "channel", "is_read"]
    ordering_fields = ["created_at", "updated_at"]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Notification.objects.all()
        return Notification.objects.filter(user=user)  # type: ignore


class UnreadNotificationCountView(GenericAPIView):
    serializer_class = UnreadNotificationCountSerializer

    def get(self, request, *args, **kwargs):
        user = request.user
        count = Notification.objects.filter(user=user, is_read=False).count()
        serializer = UnreadNotificationCountSerializer({"count": count})
        return Response(serializer.data)


class MarkNotificationsReadView(GenericAPIView):
    serializer_class = MarkNotificationsReadSerializer

    def patch(self, request, *args, **kwargs):
        serializer = MarkNotificationsReadSerializer(data=request.data)
        if serializer.is_valid():
            is_read = serializer.validated_data["is_read"]
            user = request.user
            Notification.objects.filter(user=user).update(is_read=is_read)
            return Response(
                {"message": "Notifications updated successfully."},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.generics import ListAPIView

from notifications.models import Notification
from notifications.serializers import NotificationListSerializer


class NotificationListView(ListAPIView):
    "List Notifications"

    queryset = Notification.objects.all()
    serializer_class = NotificationListSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    search_fields = ["receiving_party", "user"]
    filterset_fields = ["type", "channel", "is_visible_in_app", "is_read"]
    ordering_fields = ["created_at", "updated_at"]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Notification.objects.all()
        return Notification.objects.filter(user=user, is_visible_in_app=True)  # type: ignore

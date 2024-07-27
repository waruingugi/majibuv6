from rest_framework import serializers

from notifications.models import Notification
from users.serializers import UserReadSerializer


class NotificationListSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        exclude = [
            "updated_at",
            "type",
            "provider",
            "receiving_party",
            "external_response",
            "channel",
        ]

    def get_user(self, obj) -> None | dict:
        if obj.user is None:
            return None
        return UserReadSerializer(obj.user).data


class UnreadNotificationCountSerializer(serializers.Serializer):
    count = serializers.IntegerField()


class MarkNotificationsReadSerializer(serializers.Serializer):
    is_read = serializers.BooleanField()

from rest_framework import serializers

from notifications.models import Notification
from users.serializers import UserReadSerializer


class NotificationListSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        exclude = [
            "updated_at",
            "provider",
            "receiving_party",
            "is_visible_in_app",
            "external_response",
            "channel",
        ]

    def get_user(self, obj):
        if obj.user is None:
            return None
        return UserReadSerializer(obj.user).data

from django.contrib.auth import get_user_model
from django.db import models

from commons.models import Base
from notifications.constants import (
    NotificationChannels,
    NotificationProviders,
    NotificationTypes,
)

User = get_user_model()


class Notification(Base):
    type = models.CharField(
        max_length=255, choices=[(type, type.value) for type in NotificationTypes]
    )
    message = models.CharField(max_length=255, null=False)
    channel = models.CharField(
        max_length=255,
        choices=[(channel, channel.value) for channel in NotificationChannels],
    )
    provider = models.CharField(
        max_length=255,
        choices=[(provider, provider.value) for provider in NotificationProviders],
    )
    receiving_party = models.CharField(
        max_length=255,
        null=False,
        default="All users",
        help_text=(
            "The user id, phone number or any identification of the receiving party."
        ),
    )
    is_visible_in_app = models.BooleanField(default=True)
    is_read = models.BooleanField(default=False)
    external_response = models.JSONField(null=True, blank=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="notifications",
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.type} - {self.message}"

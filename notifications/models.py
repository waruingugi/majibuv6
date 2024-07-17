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
    phone = models.CharField(max_length=255, null=False)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        default=None,
        related_name="notifications",
    )

    def __str__(self) -> str:
        return f"{self.type} - {self.message}"

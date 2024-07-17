from django.contrib.auth import get_user_model

from commons.tests.base_tests import BaseUserAPITestCase
from notifications.constants import (
    Messages,
    NotificationChannels,
    NotificationProviders,
    NotificationTypes,
)
from notifications.models import Notification

User = get_user_model()


class NotificationModelTestCase(BaseUserAPITestCase):
    def setUp(self) -> None:
        self.user = self.create_user()
        self.notification = Notification.objects.create(
            type=NotificationTypes.OTP.value,
            message=Messages.OTP_SMS.value.format("4578"),
            channel=NotificationChannels.SMS.value,
            provider=NotificationProviders.HOSTPINNACLESMS.value,
            receiving_party=str(self.user.phone_number),
            user=self.user,
        )

    def test_notification_creates_model_instances_successfully(self) -> None:
        notification = self.notification
        self.assertTrue(isinstance(notification, Notification))
        self.assertEqual(
            str(notification), f"{notification.type} - {notification.message}"
        )
        self.assertEqual(notification.type, NotificationTypes.OTP.value)
        self.assertEqual(notification.message, Messages.OTP_SMS.value.format("4578"))
        self.assertEqual(notification.channel, NotificationChannels.SMS.value)
        self.assertEqual(
            notification.provider, NotificationProviders.HOSTPINNACLESMS.value
        )
        self.assertEqual(notification.receiving_party, str(self.user.phone_number))
        self.assertEqual(notification.user, self.user)

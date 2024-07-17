import requests
from django.conf import settings
from rest_framework import status

from commons.raw_logger import logger
from notifications.constants import NotificationChannels, NotificationProviders
from notifications.models import Notification


class OneSignalPush:
    def __init__(self) -> None:
        self.url = "https://api.onesignal.com/notifications"
        self.message = ""
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {settings.ONESIGNAL_API_KEY}",
        }
        self.push_notification_name = "Majibu In-APP Push"
        self.payload = {
            "app_id": f"{settings.ONESIGNAL_APP_ID}",
            "contents": {},
            "headings": {"en": ""},
            "name": self.push_notification_name,
            "include_external_user_ids": [],
            "target_channel": "push",
            "small_icon": "majibu_xs_logo",
        }

    def send_push(
        self, *, type: str, title: str, message: str, user_ids: list[str]
    ) -> bool:
        """A code snippet in the app identifies users and sends their user_id to Onesignal.
        We then use the user_id to specify who the message is being sent to."""
        logger.info(f"Sending PUSH notification to {user_ids}")
        self.payload["contents"] = {"en": message}
        self.payload["headgins"] = {"en": title}
        self.payload["include_external_user_ids"] = user_ids

        try:
            notification_obj = Notification.objects.create(
                type=type,
                message=message,
                channel=NotificationChannels.PUSH.value,
                provider=NotificationProviders.ONESIGNAL.value,
                receiving_party=str([user_ids]),
            )

            response = requests.post(self.url, json=self.payload, headers=self.headers)
            notification_obj.objects.update(external_response=response.json())

            if response.status_code == status.HTTP_200_OK:
                logger.info(f"Push notification to {user_ids} sent successfully.")
                return True

            return False

        except Exception as e:
            logger.error(f"Exceptioon occured while sending push to {user_ids}: {e}")
            return False


OneSignal = OneSignalPush()

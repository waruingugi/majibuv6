import requests
from django.conf import settings


class OneSignal:
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
            "contents": {
                "en": "",
            },
            "headings": {"en": ""},
            "name": self.push_notification_name,
            "include_external_user_ids": [],
            "target_channel": "push",
            "small_icon": "majibu_xs_logo",
        }

    def send_push(self, *, title: str, message: str, user_ids: list[str]) -> dict:
        response = requests.post(self.url, json=self.payload, headers=self.headers)
        return response.json()


OneSignalPush = OneSignal()

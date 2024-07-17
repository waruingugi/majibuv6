from abc import ABC, abstractmethod

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from phonenumbers import parse
from rest_framework import status

from commons.raw_logger import logger
from notifications.constants import NotificationChannels, NotificationProviders
from notifications.models import Notification

User = get_user_model()


class SMSProvider(ABC):
    @abstractmethod
    def send_sms(self, phone_number: str, type: str, message: str) -> bool:
        pass


class HostPinnacle(SMSProvider):
    def __init__(self) -> None:
        self.url = "https://smsportal.hostpinnacle.co.ke/SMSApi/send"
        self.user = None
        self.headers = {
            "Content-Type": "application/json",
        }
        self.sms_payload: dict[str, str] = {
            "userid": settings.HOST_PINNACLE_USER_ID,
            "password": settings.HOST_PINNACLE_PASSWORD,
            "mobile": "",
            "senderid": settings.HOST_PINNACLE_SENDER_ID,
            "msg": "",
            "sendMethod": "quick",
            "msgType": "text",
            "output": "json",
            "duplicatecheck": "true",
        }

    def format_phone_number(self, phone) -> str:
        """
        HostPinnacle requires numbers without a leading + sign.
        Example: 254704302356
        """
        parsed_phone = parse(phone)
        return f"{parsed_phone.country_code}{parsed_phone.national_number}"

    def send_sms(self, phone_number: str, type: str, message: str) -> bool:
        logger.info(f"Sending {type} SMS to {phone_number}...")
        self.sms_payload["mobile"] = self.format_phone_number(phone_number)
        self.sms_payload["msg"] = message

        try:
            self.user = User.objects.filter(phone_number=phone_number).first()
            notification_obj = Notification.objects.create(
                type=type,
                message=message,
                channel=NotificationChannels.SMS.value,
                provider=NotificationProviders.HOSTPINNACLESMS.value,
                receiving_party=phone_number,
                user=self.user,
            )

            response = requests.post(
                url=self.url,
                headers=self.headers,
                json=self.sms_payload,
            )
            notification_obj.objects.update(external_response=response.json())

            if response.status_code == status.HTTP_200_OK:
                logger.info(f"SMS to {phone_number} sent successfully.")
                return True

            return False

        except Exception as e:
            logger.error(f"Exceptioon occured while sending SMS to {phone_number}: {e}")
            return False


HostPinnacleSMS = HostPinnacle()

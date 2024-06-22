from abc import ABC, abstractmethod

import requests
from phonenumbers import parse
from rest_framework import status


class SMSProvider(ABC):
    @abstractmethod
    def send_sms(self, phone_number: str, message: str) -> bool:
        pass


class HostPinnacle(SMSProvider):
    def __init__(self) -> None:
        self.user_id = ""
        self.password = ""
        self.sender_id = ""
        self.base_sms_url = ""
        self.headers = {
            "Content-Type": "application/json",
        }
        self.sms_payload: dict[str, str] = {
            "userid": self.user_id,
            "password": self.password,
            "mobile": "",
            "senderid": self.sender_id,
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

    def send_sms(self, phone_number: str, message: str) -> bool:
        self.sms_payload["mobile"] = self.format_phone_number(phone_number)
        self.sms_payload["msg"] = message

        try:
            response = requests.post(
                url=f"{self.base_sms_url}/SMSApi/send",
                headers=self.headers,
                json=self.sms_payload,
            )

            if response.status_code == status.HTTP_200_OK:
                return True

            return False

        except Exception:
            return False


HostPinnacleSMS = HostPinnacle()

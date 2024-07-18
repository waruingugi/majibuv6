from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model

from commons.tests.base_tests import BaseUserAPITestCase
from notifications.constants import Messages, NotificationTypes, PushNotifications
from notifications.models import Notification
from notifications.push import OneSignal
from notifications.sms import HostPinnacleSMS

User = get_user_model()


class OneSignalPushTest(BaseUserAPITestCase):
    def setUp(self) -> None:
        self.user = self.create_user()
        self.push_service = OneSignal

    @patch("notifications.push.requests.post")
    def test_send_push_success(self, mock_post_request) -> None:
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_post_request.return_value = mock_response

        # Act
        result = self.push_service.send_push(
            type=NotificationTypes.MARKETING.value,
            title=PushNotifications.WELCOME_MESSAGE.title,
            message=PushNotifications.WELCOME_MESSAGE.message,
            user_id=str(self.user.id),
        )

        # Assert
        self.assertTrue(result)
        mock_post_request.assert_called_once_with(
            self.push_service.url,
            json=self.push_service.payload,
            headers=self.push_service.headers,
        )

        notification = Notification.objects.get(user=self.user)
        self.assertEqual(
            notification.message, PushNotifications.WELCOME_MESSAGE.message
        )

    @patch("notifications.push.requests.post")
    def test_send_push_failure(self, mock_post_request) -> None:
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"status": "error"}
        mock_post_request.return_value = mock_response

        # Act
        result = self.push_service.send_push(
            type=NotificationTypes.MARKETING.value,
            title=PushNotifications.WELCOME_MESSAGE.title,
            message=PushNotifications.WELCOME_MESSAGE.message,
            user_id=str(self.user.id),
        )

        # Assert
        self.assertFalse(result)
        mock_post_request.assert_called_once_with(
            self.push_service.url,
            json=self.push_service.payload,
            headers=self.push_service.headers,
        )

        notification = Notification.objects.get(user=self.user)
        self.assertEqual(
            notification.message, PushNotifications.WELCOME_MESSAGE.message
        )


class HostPinnacleTest(BaseUserAPITestCase):
    def setUp(self) -> None:
        # Set up any necessary initial data
        self.user = self.create_user()
        self.sms_service = HostPinnacleSMS

    @patch("notifications.sms.requests.post")
    def test_send_sms_success(self, mock_post_request) -> None:
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_post_request.return_value = mock_response

        # Act
        result = self.sms_service.send_sms(
            phone_number=str(self.user.phone_number),
            type=NotificationTypes.OTP.value,
            message=Messages.OTP_SMS.value,
        )

        # Assert
        self.assertTrue(result)
        mock_post_request.assert_called_once()

        notification = Notification.objects.get(user=self.user)
        self.assertEqual(notification.message, Messages.OTP_SMS.value)

    @patch("notifications.sms.requests.post")
    def test_send_sms_failure(self, mock_post_request) -> None:
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"status": "error"}
        mock_post_request.return_value = mock_response

        # Act
        result = self.sms_service.send_sms(
            phone_number=str(self.user.phone_number),
            type=NotificationTypes.OTP.value,
            message=Messages.OTP_SMS.value,
        )

        # Assert
        self.assertFalse(result)
        mock_post_request.assert_called_once()

        notification = Notification.objects.get(user=self.user)
        self.assertEqual(notification.message, Messages.OTP_SMS.value)

    @patch("notifications.sms.requests.post")
    def test_send_sms_exception(self, mock_post_request) -> None:
        # Arrange
        mock_post_request.side_effect = Exception("Network error")

        # Act
        result = self.sms_service.send_sms(
            phone_number=str(self.user.phone_number),
            type=NotificationTypes.OTP.value,
            message=Messages.OTP_SMS.value,
        )

        # Assert
        self.assertFalse(result)
        mock_post_request.assert_called_once()
        notification = Notification.objects.get(user=self.user)
        self.assertEqual(notification.message, Messages.OTP_SMS.value)

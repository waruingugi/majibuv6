from rest_framework import status
from rest_framework.reverse import reverse

from commons.tests.base_tests import BaseUserAPITestCase
from notifications.constants import (
    NotificationChannels,
    NotificationProviders,
    NotificationTypes,
)
from notifications.models import Notification


class NotificationListViewTests(BaseUserAPITestCase):
    def setUp(self) -> None:
        self.user = self.create_user()
        self.foreign_user = self.create_foreign_user()

        self.notification1 = Notification.objects.create(
            type=NotificationTypes.MARKETING.value,
            message="Test message 1",
            channel=NotificationChannels.SMS.value,
            provider=NotificationProviders.HOSTPINNACLESMS.value,
            receiving_party=str(self.foreign_user.id),
            user=self.foreign_user,
            is_read=False,
        )
        self.notification2 = Notification.objects.create(
            type=NotificationTypes.SESSION.value,
            message="Test message 2",
            channel=NotificationChannels.PUSH.value,
            provider=NotificationProviders.ONESIGNAL.value,
            receiving_party=str(self.user.id),
            user=self.user,
            is_read=False,
        )
        self.notification3 = Notification.objects.create(
            type=NotificationTypes.DEPOSIT.value,
            message="Test message 3",
            channel=NotificationChannels.PUSH.value,
            provider=NotificationProviders.ONESIGNAL.value,
            receiving_party=str(self.user.id),
            user=self.user,
            is_read=True,
        )

        self.force_authenticate_staff_user()
        self.list_url = reverse("notifications:notification-list")

    def test_staff_can_list_notifications(self) -> None:
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)

    def test_staff_can_search_notifications(self) -> None:
        self.force_authenticate_staff_user()
        response = self.client.get(self.list_url, {"search": str(self.foreign_user.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["message"],
            self.notification1.message,
        )

    def test_user_can_list_their_own_notifications(self) -> None:
        self.force_authenticate_user()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_expected_fields_exist_in_response(self) -> None:
        self.force_authenticate_user()
        response = self.client.get(self.list_url)
        result_in = response.data["results"][0]
        self.assertIn("created_at", result_in)
        self.assertIn("id", result_in)
        self.assertIn("message", result_in)
        self.assertIn("is_read", result_in)

    def test_unread_notifications_count_is_correct(self) -> None:
        self.force_authenticate_user()
        response = self.client.get(reverse("notifications:count-unread"))
        self.assertEqual(1, response.data["count"])

    def test_mark_notifications_as_read(self) -> None:
        self.force_authenticate_user()
        response = self.client.patch(
            reverse("notifications:update-read"), data={"is_read": True}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            0, Notification.objects.filter(is_read=False, user=self.user).count()
        )
        self.assertEqual(2, Notification.objects.filter(user=self.user).count())

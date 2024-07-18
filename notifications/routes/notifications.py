from django.urls import path

from notifications.views.notifications import (
    MarkNotificationsReadView,
    NotificationListView,
    UnreadNotificationCountView,
)

app_name = "notifications"

urlpatterns = [
    path(
        "notifications/",
        NotificationListView.as_view(),
        name="notification-list",
    ),
    path(
        "notifications/count-unread",
        UnreadNotificationCountView.as_view(),
        name="count-unread",
    ),
    path(
        "notifications/update-read/",
        MarkNotificationsReadView.as_view(),
        name="update-read",
    ),
]

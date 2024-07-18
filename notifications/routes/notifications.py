from django.urls import path

from notifications.views.notifications import NotificationListView

app_name = "notifications"

urlpatterns = [
    path(
        "notifications/",
        NotificationListView.as_view(),
        name="notification-list",
    ),
]

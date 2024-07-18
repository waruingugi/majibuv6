from django.urls import include, path

from notifications.routes import notifications

urlpatterns = [
    path("", include((notifications.urlpatterns, "notifications"))),
]

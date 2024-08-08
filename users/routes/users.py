from django.urls import path

from users.views.users import (
    LatestAppVersionView,
    UserCreateView,
    UserListView,
    UserRetrieveUpdateView,
)

app_name = "users"

urlpatterns = [
    path(
        "latest-app-version", LatestAppVersionView.as_view(), name="latest-app-version"
    ),
    path("create/", UserCreateView.as_view(), name="user-create"),
    path("", UserListView.as_view(), name="user-list"),
    path("<str:id>/", UserRetrieveUpdateView.as_view(), name="user-detail"),
]

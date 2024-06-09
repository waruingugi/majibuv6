from django.urls import path

from users.views import (
    UserCreateAPIView,
    UserDeleteAPIView,
    UserListAPIView,
    UserRetrieveUpdateAPIView,
)

app_name = "users"

urlpatterns = [
    path("users/create/", UserCreateAPIView.as_view(), name="user-create"),
    path("users/list/", UserListAPIView.as_view(), name="user-list"),
    path("users/<str:id>/", UserRetrieveUpdateAPIView.as_view(), name="user-detail"),
    path("users/<str:id>/delete/", UserDeleteAPIView.as_view(), name="user-delete"),
]

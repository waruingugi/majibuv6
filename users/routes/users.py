from django.urls import path

from users.views.users import UserCreateView, UserListView, UserRetrieveUpdateView

app_name = "users"

urlpatterns = [
    path("users/create/", UserCreateView.as_view(), name="user-create"),
    path("users/", UserListView.as_view(), name="user-list"),
    path("users/<str:id>/", UserRetrieveUpdateView.as_view(), name="user-detail"),
]

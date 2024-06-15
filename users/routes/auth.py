from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.views.auth import RegisterView

app_name = "auth"

urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="obtain-token"),
    path("token/refresh/", TokenRefreshView.as_view(), name="refresh-token"),
    path("register/", RegisterView.as_view(), name="register"),
]

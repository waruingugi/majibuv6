from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.views.auth import OTPVerificationView, RegisterView

app_name = "auth"

urlpatterns = [
    path("login/", TokenObtainPairView.as_view(), name="obtain-token"),
    path("token/refresh/", TokenRefreshView.as_view(), name="refresh-token"),
    path("register/", RegisterView.as_view(), name="register"),
    path("verify-otp/", OTPVerificationView.as_view(), name="verify-otp"),
]

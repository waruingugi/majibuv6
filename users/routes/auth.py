from django.urls import path
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.views.auth import OTPVerificationView, RegisterView

# Extend the schema for the TokenObtainPairView
TokenObtainPairView = extend_schema_view(post=extend_schema(tags=["auth"]))(  # type: ignore
    TokenObtainPairView
)

# Extend the schema for the TokenRefreshView
TokenRefreshView = extend_schema_view(  # type: ignore
    post=extend_schema(
        tags=["auth"],
    )
)(TokenRefreshView)

app_name = "auth"

urlpatterns = [
    path("login/", TokenObtainPairView.as_view(), name="obtain-token"),
    path("token/refresh/", TokenRefreshView.as_view(), name="refresh-token"),
    path("register/", RegisterView.as_view(), name="register"),
    path("verify-otp/", OTPVerificationView.as_view(), name="verify-otp"),
]

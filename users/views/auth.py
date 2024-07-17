from django.core.cache import cache
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from commons.raw_logger import logger
from commons.tasks import send_sms
from commons.throttles import AuthenticationThrottle
from commons.utils import md5_hash
from notifications.constants import Messages, NotificationTypes
from users.models import User
from users.otp import create_otp
from users.serializers import (
    OTPVerificationSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    ResendOTPVerificationSerializer,
    UserCreateSerializer,
    UserTokenObtainPairSerializer,
)


@extend_schema(tags=["auth"])
class UserTokenObtainPairView(TokenObtainPairView):
    serializer_class = UserTokenObtainPairSerializer  # type: ignore


@extend_schema(tags=["auth"])
class RegisterView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    throttle_classes = [AuthenticationThrottle]
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        phone_number = str(user.phone_number)
        otp = create_otp(phone_number)
        # TODO: Remove
        logger.info(f"Sending {otp} to {phone_number}")

        message = Messages.OTP_SMS.value.format(otp)
        send_sms.delay(
            phone_number=phone_number, type=NotificationTypes.OTP.value, message=message
        )

        return user


@extend_schema(tags=["auth"])
class ResendOTPVerificationView(GenericAPIView):
    serializer_class = ResendOTPVerificationSerializer
    permission_classes = [AllowAny]
    throttle_classes = [AuthenticationThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data["phone_number"]
            otp = create_otp(phone_number)

            # TODO: Remove
            logger.info(f"Sending {otp} to {phone_number}")

            message = Messages.OTP_SMS.value.format(otp)
            send_sms.delay(
                phone_number=phone_number,
                type=NotificationTypes.OTP.value,
                message=message,
            )

            return Response(
                {"detail": "OTP sent successfully"}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["auth"])
class OTPVerificationView(GenericAPIView):
    serializer_class = OTPVerificationSerializer
    permission_classes = [AllowAny]
    throttle_classes = [AuthenticationThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data["phone_number"]

            # Activate user
            user = User.objects.get(phone_number=phone_number)
            user.is_verified = True
            user.save()

            # Clear OTP from cache
            cache.delete(md5_hash(phone_number))

            return Response(
                {"detail": "User activated successfully."}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["auth"])
class PasswordResetRequestView(GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data["phone_number"]

            otp = create_otp(phone_number)
            # TODO: Remove
            logger.info(f"Sending {otp} to {phone_number}")

            message = Messages.OTP_SMS.value.format(otp)
            send_sms.delay(
                phone_number=phone_number,
                type=NotificationTypes.OTP.value,
                message=message,
            )

            return Response(
                {"detail": "OTP has been sent to your phone number."},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["auth"])
class PasswordResetConfirmView(GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data["phone_number"]
            user = User.objects.get(phone_number=phone_number)
            user.set_password(serializer.validated_data["new_password"])

            user.is_active = True  # Make the user active if necessary
            user.save()

            # Clear OTP from cache
            cache.delete(md5_hash(phone_number))

            return Response(
                {"detail": "Password has been reset successfully."},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

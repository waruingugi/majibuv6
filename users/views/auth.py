from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.response import Response

from commons.tasks import send_sms
from commons.throttles import RegisterThrottle
from commons.utils import md5_hash
from users.constants import OTP_SMS
from users.models import User
from users.otp import create_otp
from users.serializers import OTPVerificationSerializer, UserCreateSerializer


class RegisterView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    throttle_classes = [RegisterThrottle]

    def perform_create(self, serializer):
        user = serializer.save()
        phone_number = str(user.phone_number)
        otp = create_otp(phone_number)

        send_sms.delay(phone_number, OTP_SMS.format(otp))

        return user


class OTPVerificationView(GenericAPIView):
    serializer_class = OTPVerificationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data["phone_number"]

            # Activate user
            user = get_object_or_404(User, phone_number=phone_number)
            user.is_verified = True
            user.save()

            # Clear OTP from cache
            cache.delete(md5_hash(phone_number))

            return Response(
                {"detail": "User activated successfully."}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

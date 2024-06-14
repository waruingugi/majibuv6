from rest_framework.generics import CreateAPIView

from commons.tasks import send_sms
from users.constants import OTP_SMS
from users.models import User
from users.otp import create_otp
from users.serializers import UserCreateSerializer


class RegisterView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        otp = create_otp(user.phone_number)

        send_sms.delay(user.phone_number, OTP_SMS.format(otp))

        return user

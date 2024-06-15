from rest_framework.generics import CreateAPIView

from commons.tasks import send_sms
from commons.throttles import RegisterThrottle
from users.constants import OTP_SMS
from users.models import User
from users.otp import create_otp
from users.serializers import UserCreateSerializer


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

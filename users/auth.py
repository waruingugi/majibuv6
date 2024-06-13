from rest_framework.generics import CreateAPIView

from users.models import User
from users.serializers import UserCreateSerializer


class RegisterView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer

    def perform_create(self, serializer):
        # user = serializer.save()
        return super().perform_create(serializer)

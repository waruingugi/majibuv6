from rest_framework.generics import GenericAPIView

from users.models import User
from users.serializers import UserSerializer


class UserBaseView(GenericAPIView):
    "The parent view defining common functionality in user views."

    queryset = User.objects.all()
    serializer_class = UserSerializer

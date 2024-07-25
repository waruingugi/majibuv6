# views.py
from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from commons.utils import is_business_open
from user_sessions.serializers import AvialableSessionSerializer


@extend_schema(tags=["sessions"])
class BusinessHoursView(GenericAPIView):
    def get(self, request):
        data = {"is_open": is_business_open()}
        return Response(data, status=status.HTTP_200_OK)


@extend_schema(tags=["sessions"])
class SessionDetailsView(GenericAPIView):
    def get(self, request):
        data = {
            "questions": settings.QUESTIONS_IN_SESSION,
            "seconds": settings.SESSION_DURATION,
            "stake": settings.SESSION_STAKE,
            "payout": (settings.SESSION_PAYOUT_RATIO * settings.SESSION_STAKE),
        }

        return Response(data, status=status.HTTP_200_OK)


@extend_schema(tags=["sessions"])
class AvailableSessionView(GenericAPIView):
    serializer_class = AvialableSessionSerializer

    def post(self, request, *args, **kwargs):
        """
        Users post to this endpoint to receive a session id that they will
        play.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            pass

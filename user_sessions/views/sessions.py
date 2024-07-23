# views.py
from datetime import datetime

from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response


@extend_schema(tags=["sessions"])
class BusinessHoursView(GenericAPIView):
    def get(self, request):
        eat_now = datetime.now()
        is_open = False

        # Extract the time components from open_time and close_time
        open_hour, open_minute = map(int, settings.BUSINESS_OPENS_AT.split(":"))
        close_hour, close_minute = map(int, settings.BUSINESS_CLOSES_AT.split(":"))

        # Create datetime objects for the current time, open time, and close time
        current_datetime = datetime(
            year=eat_now.year,
            month=eat_now.month,
            day=eat_now.day,
            hour=eat_now.hour,
            minute=eat_now.minute,
        )
        business_opens_at = datetime(
            year=eat_now.year,
            month=eat_now.month,
            day=eat_now.day,
            hour=open_hour,
            minute=open_minute,
        )
        business_closes_at = datetime(
            year=eat_now.year,
            month=eat_now.month,
            day=eat_now.day,
            hour=close_hour,
            minute=close_minute,
        )

        # Check if the current time is within the specified range
        # AND that fall-back variable BUSINESS_IS_OPEN is true.
        if (business_opens_at <= current_datetime <= business_closes_at) and (
            settings.BUSINESS_IS_OPEN
        ):
            is_open = True

        data = {
            "is_open": is_open,
            "opens_at": business_opens_at.strftime("%I:%M%p"),
            "closes_at": business_closes_at.strftime("%I:%M%p"),
        }

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

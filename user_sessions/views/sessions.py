# views.py

from datetime import datetime, timedelta

from django.conf import settings
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from commons.errors import ErrorCodes
from commons.utils import is_business_open
from quiz.models import Result
from user_sessions.constants import AVAILABLE_SESSION_EXPIRY_TIME, SESSION_BUFFER_TIME
from user_sessions.models import Session
from user_sessions.serializers import (
    AvialableSessionSerializer,
    QuizRequestSerializer,
    QuizResponseSerializer,
)
from user_sessions.utils import compose_quiz, get_available_session


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
            user = request.user
            category = serializer.validated_data["category"]
            available_session_id = get_available_session(user=user, category=category)

            if not available_session_id:
                raise serializers.ValidationError(
                    {"detail": ErrorCodes.NO_AVAILABLE_SESSION.value}
                )

            cache_key = f"{request.user.id}:available_session_id"
            cache.set(
                cache_key,
                str(available_session_id),
                timeout=AVAILABLE_SESSION_EXPIRY_TIME,
            )

            return Response({"id": available_session_id}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["sessions"])
class QuizView(GenericAPIView):
    serializer_class = QuizRequestSerializer

    def post(self, request, *args, **kwargs):
        """A very critical endpoint.
        We compile and serve the questions a user will answer.
        In the background, we reduce the user's wallet."""

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            session = get_object_or_404(
                Session, id=serializer.validated_data["session_id"]
            )
            user = request.user

            quiz_data = compose_quiz(str(session.id))
            expires_at = datetime.now() + timedelta(
                seconds=(SESSION_BUFFER_TIME + settings.SESSION_DURATION)
            )
            result = Result.objects.create(
                user=user, session=session, expires_at=expires_at
            )

            response_data = {
                "count": settings.QUESTIONS_IN_SESSION,
                "user_id": str(user.id),
                "session_id": str(session.id),
                "duration": settings.SESSION_DURATION,
                "result_id": str(result.id),
                "result": quiz_data,
            }
            response_serializer = QuizResponseSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

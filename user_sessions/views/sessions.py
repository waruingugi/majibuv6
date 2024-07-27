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
    BusinessHoursSerializer,
    QuizRequestSerializer,
    QuizResponseSerializer,
    QuizSubmissionSerializer,
    SessionDetailsSerializer,
)
from user_sessions.utils import CalculateUserScore, compose_quiz, get_available_session


@extend_schema(tags=["sessions"])
class BusinessHoursView(GenericAPIView):
    serializer_class = BusinessHoursSerializer

    def get(self, request):
        data = {"is_open": is_business_open()}
        serializer = BusinessHoursSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(tags=["sessions"])
class SessionDetailsView(GenericAPIView):
    serializer_class = SessionDetailsSerializer

    def get(self, request):
        data = {
            "questions": settings.QUESTIONS_IN_SESSION,
            "seconds": settings.SESSION_DURATION,
            "stake": settings.SESSION_STAKE,
            "payout": (settings.SESSION_PAYOUT_RATIO * settings.SESSION_STAKE),
        }

        serializer = SessionDetailsSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
class QuizRequestView(GenericAPIView):
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
                "duration": (settings.SESSION_DURATION * 1000),  # In milliseconds
                "result_id": str(result.id),
                "result": quiz_data,
            }
            # response_data = {
            #     'count': 5,
            #     'user_id': '6cb71b02-fcca-4603-814a-60955e682242',
            #     'session_id': '9e41dd3a-c9f7-4ac8-8ac9-2d009df81d92',
            #     'duration': 30,
            #     'result_id': '42258723-0f10-4a6c-95ca-d3d681bd53f2',
            #     'result': [
            #         {
            #             'id': '11f64cd1-2dfe-407d-bbe4-b0d0d3f7ec8e',
            #             'question_text': 'What is the capital of France?',
            #             'choices': [
            #                 {
            #                     'id': '1018090e-d11f-4922-99a9-7966e84baaf9',
            #                     'question_id': '11f64cd1-2dfe-407d-bbe4-b0d0d3f7ec8e',
            #                     'choice_text': 'London'
            #                 },
            #                 {
            #                     'id': 'da7e5187-8efa-43c7-b2ed-ae108e18c77b',
            #                     'question_id': '11f64cd1-2dfe-407d-bbe4-b0d0d3f7ec8e',
            #                     'choice_text': 'Paris'
            #                 }
            #             ]
            #         },
            #         {
            #             'id': '58d64a90-0166-4f4d-aa53-0eed88361274',
            #             'question_text': 'What is 2+2?',
            #             'choices': [
            #                 {
            #                     'id': '3387f156-6749-4f9e-80ee-b06fa3794573',
            #                     'question_id': '58d64a90-0166-4f4d-aa53-0eed88361274',
            #                     'choice_text': '22'
            #                 },
            #                 {
            #                     'id': '108d36f2-d708-4a6c-ba09-e65de1c0f6e8',
            #                     'question_id': '58d64a90-0166-4f4d-aa53-0eed88361274',
            #                     'choice_text': '4'
            #                 }
            #             ]
            #         }
            #     ]
            # }

            response_serializer = QuizResponseSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["sessions"])
class QuizSubmissionView(GenericAPIView):
    serializer_class = QuizSubmissionSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            choices = serializer.validated_data["choices"]
            result_id = serializer.validated_data["result_id"]

            CalculateUserScore.calculate_score(
                user=request.user, result_id=result_id, choices=choices
            )
            return Response(
                {"message": "Choices submitted successfully"}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

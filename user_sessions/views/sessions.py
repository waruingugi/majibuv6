# views.py


from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, serializers, status
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.response import Response

from commons.errors import ErrorCodes
from commons.pagination import StandardPageNumberPagination
from commons.permissions import IsStaffOrSelfPermission
from commons.utils import is_business_open
from user_sessions.constants import AVAILABLE_SESSION_EXPIRY_TIME
from user_sessions.models import DuoSession
from user_sessions.serializers import (
    AvialableSessionSerializer,
    BusinessHoursSerializer,
    SessionDetailsSerializer,
    StaffDuoSessionListSerializer,
    UserDuoSessionListSerializer,
)
from user_sessions.utils import get_available_session


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


class DuoSessionListView(ListAPIView):
    """Retrieve a user."""

    queryset = DuoSession.objects.all()
    permission_classes = [IsStaffOrSelfPermission]
    pagination_class = StandardPageNumberPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    search_fields = [
        "id",
        "party_a__phone_number",
        "party_b__phone_number",
        "winner__phone_number",
    ]
    filterset_fields = ["status"]
    ordering_fields = ["created_at"]

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return StaffDuoSessionListSerializer
        return UserDuoSessionListSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return DuoSession.objects.all()
        return DuoSession.objects.filter(
            Q(party_a=user) | Q(party_b=user) | Q(winner=user)
        )

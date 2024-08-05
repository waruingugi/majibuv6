# views.py


from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, serializers, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveAPIView
from rest_framework.response import Response

from commons.errors import ErrorCodes
from commons.pagination import StandardPageNumberPagination
from commons.permissions import IsDuoSessionPlayer, IsStaffOrSelfPermission
from commons.utils import is_business_open
from user_sessions.constants import AVAILABLE_SESSION_EXPIRY_TIME
from user_sessions.models import DuoSession
from user_sessions.serializers import (
    AvialableSessionSerializer,
    BusinessHoursSerializer,
    DuoSessionDetailsSerializer,
    MobileAdSerializer,
    SessionDetailsSerializer,
    StaffDuoSessionListSerializer,
    UserDuoSessionListSerializer,
)
from user_sessions.utils import get_available_session, get_duo_session_details


@extend_schema(tags=["sessions"])
class BusinessHoursView(GenericAPIView):
    "Is Business Open? endpoint"

    serializer_class = BusinessHoursSerializer

    def get(self, request):
        data = {"is_open": is_business_open()}
        serializer = BusinessHoursSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(tags=["sessions"])
class SessionDetailsView(GenericAPIView):
    "Session details (questions, stake, e.t.c)"

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
    """Returns a session id which is then used to receive a quiz."""

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
    """List DuoSessions"""

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
        return DuoSession.objects.filter(Q(party_a=user) | Q(party_b=user))


@extend_schema(tags=["sessions"])
class DuoSessionDetailsView(RetrieveAPIView):
    """DuoSession details (results for party_a and party_b)"""

    lookup_field = "id"
    serializer_class = DuoSessionDetailsSerializer
    permission_classes = [IsDuoSessionPlayer]

    def get_object(self):
        user = self.request.user
        duo_session_id = self.kwargs.get("id")

        try:
            DuoSession.objects.get(
                Q(id=duo_session_id) & (Q(party_a=user) | Q(party_b=user))
            )
        except DuoSession.DoesNotExist:
            raise PermissionDenied(ErrorCodes.INVALID_DUOSESSION.value)

        return get_duo_session_details(user=user, duo_session_id=duo_session_id)

    def retrieve(self, request, *args, **kwargs):
        duo_session_details = self.get_object()  # type: ignore
        return Response(duo_session_details, status=status.HTTP_200_OK)


@extend_schema(tags=["sessions"])
class MobileAdView(GenericAPIView):
    "Image to be shown on mobile home page"

    serializer_class = MobileAdSerializer

    def get(self, request):
        data = {
            "image_url": settings.AD_IMAGE_URL,
            "redirects_to": settings.AD_REDIRECTS_TO,
        }
        serializer = MobileAdSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

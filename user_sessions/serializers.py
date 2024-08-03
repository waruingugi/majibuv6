from django.db.models import Q
from rest_framework import serializers

from commons.constants import SessionCategories
from commons.errors import ErrorCodes
from user_sessions.models import DuoSession, Session
from users.serializers import UserReadSerializer


class AvialableSessionSerializer(serializers.Serializer):
    category = serializers.ChoiceField(
        choices=[(category, category.value) for category in SessionCategories]
    )


class BusinessHoursSerializer(serializers.Serializer):
    is_open = serializers.BooleanField()


class DuoSessionDetailsSerializer(serializers.Serializer):
    id = serializers.CharField()

    def validate(self, data):
        """Validate requester is in duosession"""
        id = data.get("id")
        request = self.context.get("request")
        if not request:
            raise serializers.ValidationError(
                {"detail": ErrorCodes.CONTEXT_IS_REQUIRED.value}
            )

        user = request.user
        duo_session = DuoSession.objects.filter(
            Q(id=id) & (Q(party_a=user) | Q(party_b=user))
        )

        if not duo_session.exists():
            raise serializers.ValidationError(
                {"detail": ErrorCodes.INVALID_DUOSESSION.value}
            )


class SessionDetailsSerializer(serializers.Serializer):
    questions = serializers.IntegerField()
    seconds = serializers.IntegerField()
    stake = serializers.FloatField()
    payout = serializers.FloatField()


class SessionCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ["category"]


class BaseDuoSessionListSerializer(serializers.ModelSerializer):
    session = SessionCategorySerializer()

    class Meta:
        model = DuoSession


class StaffDuoSessionListSerializer(BaseDuoSessionListSerializer):
    party_a = UserReadSerializer()
    party_b = UserReadSerializer()
    winner = UserReadSerializer()

    class Meta(BaseDuoSessionListSerializer.Meta):
        model = DuoSession
        fields = [
            "id",
            "created_at",
            "session",
            "amount",
            "party_a",
            "party_b",
            "status",
            "winner",
        ]


class UserDuoSessionListSerializer(BaseDuoSessionListSerializer):
    class Meta(BaseDuoSessionListSerializer.Meta):
        model = DuoSession
        fields = ["id", "created_at", "session", "status", "amount"]

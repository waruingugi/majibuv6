from rest_framework import serializers

from commons.constants import SessionCategories
from user_sessions.models import DuoSession, Session
from users.serializers import UserReadSerializer


class AvialableSessionSerializer(serializers.Serializer):
    category = serializers.ChoiceField(
        choices=[(category, category.value) for category in SessionCategories]
    )


class BusinessHoursSerializer(serializers.Serializer):
    is_open = serializers.BooleanField()


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


class QuestionSerializer(serializers.Serializer):
    question = serializers.CharField()
    choice = serializers.CharField()
    is_correct = serializers.BooleanField()


class UserDetailsSerializer(serializers.Serializer):
    username = serializers.CharField()
    phone_number = serializers.CharField()
    score = serializers.DecimalField(max_digits=5, decimal_places=2)
    total_answered = serializers.IntegerField()
    total_correct = serializers.IntegerField()
    questions = QuestionSerializer(required=False, allow_null=True, many=True)


class DuoSessionDetailsSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    category = serializers.CharField()
    status = serializers.CharField()
    party_a = UserDetailsSerializer()
    party_b = UserDetailsSerializer()

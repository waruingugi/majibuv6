from rest_framework import serializers

from commons.constants import SessionCategories


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

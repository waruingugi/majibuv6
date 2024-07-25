from rest_framework import serializers

from commons.constants import SessionCategories


class AvialableSessionSerializer(serializers.Serializer):
    category = serializers.ChoiceField(
        choices=[(category, category.value) for category in SessionCategories]
    )

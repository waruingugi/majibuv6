from django.conf import settings
from django.core.cache import cache
from rest_framework import serializers

from accounts.models import Transaction
from commons.constants import SessionCategories
from commons.errors import ErrorCodes
from commons.utils import is_business_open, md5_hash
from quiz.models import Choice, Question, Result


class AvialableSessionSerializer(serializers.Serializer):
    category = serializers.ChoiceField(
        choices=[(category, category.value) for category in SessionCategories]
    )


class QuizRequestSerializer(serializers.Serializer):
    session_id = serializers.CharField()

    def validate(self, data):
        """Run 5 important checks before serving a user with a session."""
        session_id = data.get("session_id")
        request = self.context.get("request")
        if not request:
            raise serializers.ValidationError(
                {"detail": ErrorCodes.CONTEXT_IS_REQUIRED.value}
            )

        user = request.user
        available_session_id = cache.get(f"{user.id}:available_session_id")

        # 1. Assert session id exists in cache
        if (not available_session_id) or (available_session_id != session_id):
            raise serializers.ValidationError(
                {"detail": ErrorCodes.INVALID_SESSION_ID.value}
            )

        # 2. Assert business in open
        if not is_business_open():
            raise serializers.ValidationError(
                {"detail": ErrorCodes.BUSINESS_IS_CLOSED.value}
            )

        # 3. Assert no withdrawal requests are being processed
        if cache.get(md5_hash(f"{user.phone_number}:withdraw_request")):
            raise serializers.ValidationError(
                {"detail": ErrorCodes.WITHDRAWAL_REQUEST_IN_QUEUE.value}
            )

        # 4. Assert user balance is sufficient
        user_balance = Transaction.objects.get_user_balance(user=user)
        withdrawal_amount = settings.SESSION_STAKE

        if user_balance < withdrawal_amount:
            raise serializers.ValidationError(
                {
                    "detail": ErrorCodes.INSUFFICIENT_BALANCE_TO_WITHDRAW.value.format(
                        withdrawal_amount
                    )
                }
            )

        # 5. Assert no active results in the model.
        results = Result.objects.filter(user=user, is_active=True)
        if results.exists():
            raise serializers.ValidationError(
                {"detail": ErrorCodes.SESSION_IN_QUEUE.value}
            )

        return data


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ["id", "question_id", "choice_text"]


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True)

    class Meta:
        model = Question
        fields = ["id", "question_text", "choices"]


class QuizResponseSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    user_id = serializers.CharField()
    session_id = serializers.CharField()
    duration = serializers.IntegerField()
    result_id = serializers.CharField()
    result = QuestionSerializer(many=True)

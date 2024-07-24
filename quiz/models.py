from decimal import Decimal

from django.db import models

from commons.constants import SESSION_RESULT_DECIMAL_PLACES, SessionCategories, User
from commons.models import Base
from user_sessions.models import Sessions


class Questions(Base):
    """Questions Model"""

    category = models.CharField(
        max_length=255,
        choices=[(category, category.value) for category in SessionCategories],
    )
    question_text = models.TextField(null=False)

    def __str__(self):
        return self.question_text


class Choices(Base):
    """Choices Model"""

    question = models.ForeignKey(Questions, on_delete=models.CASCADE)
    choice_text = models.TextField(null=False)

    def __str__(self):
        return self.choice_text


class Answers(Base):
    """Answers Model"""

    question = models.OneToOneField(Questions, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choices, on_delete=models.CASCADE)


class UserAnswers(Base):
    """UserAnswers Model: Save user answers"""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Questions, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choices, on_delete=models.CASCADE)
    session = models.ForeignKey(Sessions, on_delete=models.CASCADE)


class Results(Base):
    """Results Model"""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session = models.ForeignKey(Sessions, on_delete=models.CASCADE)
    total_answered = models.IntegerField(
        null=True, default=0, help_text="Number of total questions answered"
    )
    total_correct = models.IntegerField(
        null=True,
        default=0,
        help_text="Number of total correctly/right answered questions",
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=SESSION_RESULT_DECIMAL_PLACES,
        null=True,
        default=Decimal(0.0),
        help_text=(
            "A combination of total_correct and total_answered fields. "
            "This is the total marks before moderation and is NOT shown to the user."
        ),
    )
    score = models.DecimalField(
        max_digits=10,
        decimal_places=SESSION_RESULT_DECIMAL_PLACES,
        null=True,
        default=Decimal(0.0),
        help_text=(
            "The total marks based on all weights, formula and other criteria. "
            "This what is shown to the user"
        ),
    )
    expires_at = models.DateTimeField(
        null=False,
        help_text="When the session expires and is no longer available to the user",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="If these results can be used to create pair with another user",
    )

    @property
    def category(self):
        return self.session.category

    def __str__(self):
        return f"Results for {self.user} in session {self.session}"

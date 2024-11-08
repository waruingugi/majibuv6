import json

from django.contrib.auth import get_user_model
from django.db import models

from commons.constants import (
    MONETARY_DECIMAL_PLACES,
    DuoSessionStatuses,
    SessionCategories,
)
from commons.models import Base

User = get_user_model()


class UserSessionStat(Base):
    """User Session Stats model"""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_wins = models.IntegerField(default=0)
    total_losses = models.IntegerField(default=0)
    sessions_played = models.IntegerField(default=0)

    @property
    def win_ratio(self) -> float:
        if self.sessions_played == 0:  # Avoids Zero DivisionError
            return 0.0
        return self.total_wins / self.sessions_played


class PoolSessionStat(Base):
    """Pool Session Statistics model"""

    total_players = models.IntegerField(null=True, default=0)
    _statistics = models.JSONField(null=True, blank=True)

    @property
    def statistics(self) -> dict:
        stats_dict = {}
        if self._statistics:
            stats_dict = json.loads(self._statistics)
        return stats_dict


class Session(Base):
    """Session model"""

    category = models.CharField(
        max_length=255,
        choices=[(category, category.value) for category in SessionCategories],
    )
    _questions = models.TextField(db_column="questions")

    @property
    def questions(self) -> list[str]:
        return self._questions.replace(" ", "").split(",")

    def __str__(self) -> str:
        return self.category


class DuoSession(Base):
    """DuoSession model"""

    party_a = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="party_a"
    )
    party_b = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="party_b"
    )
    session = models.ForeignKey(
        Session, on_delete=models.SET_NULL, null=True, default=None
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=MONETARY_DECIMAL_PLACES,
        null=True,
        help_text="This is the Amount that was transacted.",
    )
    status = models.CharField(
        max_length=255,
        null=True,
        choices=[(status, status.value) for status in DuoSessionStatuses],
    )
    winner = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="winner"
    )

    @property
    def category(self):
        return self.session.category if self.session else None

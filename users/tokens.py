from datetime import datetime, timedelta

from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken


def get_lifetime() -> timedelta:
    """Set the expiration time to midnight because we do not want
    users being logged off when playing sessions during the day."""
    refresh_lifetime = settings.SIMPLE_JWT.get("REFRESH_TOKEN_LIFETIME")
    exp_date = datetime.now() + refresh_lifetime  # type: ignore

    exp_midnight_date = datetime.combine(exp_date, datetime.max.time())
    life_time = exp_midnight_date - datetime.now()

    return life_time


class UserRefreshToken(RefreshToken):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_exp(lifetime=get_lifetime())

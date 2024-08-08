import math
from datetime import datetime
from decimal import Decimal
from hashlib import md5

from django.conf import settings

from accounts.constants import B2C_WITHDRAWAL_CHARGES, DEFAULT_B2C_CHARGE


def md5_hash(value: str) -> str:
    """Convert string value into hash"""
    return md5(value.encode()).hexdigest()


def calculate_b2c_withdrawal_charge(amount: int | float | Decimal) -> int:
    """Calculate B2C Withdrawal charge"""
    amount = math.ceil(
        amount
    )  # If float, round up to the next integer: 100.1 becomes 101
    for charge_range in B2C_WITHDRAWAL_CHARGES:
        if charge_range.min <= amount <= charge_range.max:
            return charge_range.charge
    # Default case if amount is outside defined ranges
    return DEFAULT_B2C_CHARGE


def is_business_open() -> bool:
    """Is business open to playing sessions at this time?"""
    eat_now = datetime.now()
    is_open = False

    # Extract the time components from open_time and close_time
    open_hour, open_minute = map(int, settings.BUSINESS_OPENS_AT.split(":"))
    close_hour, close_minute = map(int, settings.BUSINESS_CLOSES_AT.split(":"))

    # Create datetime objects for the current time, open time, and close time
    current_datetime = datetime(
        year=eat_now.year,
        month=eat_now.month,
        day=eat_now.day,
        hour=eat_now.hour,
        minute=eat_now.minute,
    )
    business_opens_at = datetime(
        year=eat_now.year,
        month=eat_now.month,
        day=eat_now.day,
        hour=open_hour,
        minute=open_minute,
    )
    business_closes_at = datetime(
        year=eat_now.year,
        month=eat_now.month,
        day=eat_now.day,
        hour=close_hour,
        minute=close_minute,
    )

    # Check if the current time is within the specified range
    # AND that fall-back variable BUSINESS_IS_OPEN is true.
    if (business_opens_at <= current_datetime <= business_closes_at) and (
        settings.BUSINESS_IS_OPEN
    ):
        is_open = True

    return is_open

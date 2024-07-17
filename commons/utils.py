import math
from decimal import Decimal
from hashlib import md5

from accounts.constants import B2C_WITHDRAWAL_CHARGES, DEFAULT_B2C_CHARGE
from notifications.constants import SMS_PROVIDERS


def md5_hash(value: str) -> str:
    """Convert string value into hash"""
    return md5(value.encode()).hexdigest()


def send_sms(phone_number: str, message: str) -> None:
    for provider in SMS_PROVIDERS:
        if provider.send_sms(phone_number, message):
            return

    # Raise error if all providers failed here


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

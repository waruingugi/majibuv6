from enum import Enum


class DuoSessionStatuses(str, Enum):  # Also acts as role names
    PAIRED = "PAIRED"
    REFUNDED = "REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"

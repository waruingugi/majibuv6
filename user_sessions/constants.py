from enum import Enum

AVAILABLE_SESSION_EXPIRY_TIME = 10  # In seconds
SESSION_BUFFER_TIME = 7  # In seconds


class DuoSessionStatuses(str, Enum):
    PAIRED = "PAIRED"
    REFUNDED = "REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"

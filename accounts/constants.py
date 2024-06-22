from enum import Enum


class TransactionCashFlow(str, Enum):
    INWARD = "INWARD"
    OUTWARD = "OUTWARD"


class TransactionTypes(str, Enum):
    BONUS = "BONUS"
    REFUND = "REFUND"
    REWARD = "REWARD"
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"


class TransactionStatuses(str, Enum):
    PENDING = "PENDING"
    SUCCESSFUL = "SUCCESSFUL"
    FAILED = "FAILED"

from enum import Enum

# Withdraw amount restrictions
MIN_WITHDRAWAL_AMOUNT = 20
MAX_WITHDRAWAL_AMOUNT = 1000

# You can only deposit an amount in this options
DEPOSIT_AMOUNT_CHOICES = [50, 100, 200, 500, 1000]

# M-Pesa STKPush deposit description
STKPUSH_DEPOSIT_DESCRPTION = "Deposit of Ksh {} for account {} using M-Pesa STKPush."

# M-Pesa direct paybill payment description
PAYBILL_DEPOSIT_DESCRIPTION = "Deposit of Ksh {} for account {} using M-Pesa paybill."

# M-Pesa B2C payment description
PAYBILL_B2C_DESCRIPTION = "Payment of Ksh {} for account {} using B2C payment."

# Withdrawal to play session description
SESSION_WITHDRAWAL_DESCRIPTION = "Withdrawal by user: {} for session id: {}."

# Deposit from winning a session description
SESSION_WIN_DESCRIPION = "Deposit to user: {} for winning session id: {}"

# Refund for party_a for playing a session description
REFUND_SESSION_DESCRIPTION = "Refund user: {} for playing session id: {}"

# Partially refund for party_a for playing a session description
PARTIALLY_REFUND_SESSION_DESCRIPTION = (
    "Partially refund user: {} for playing session id: {}"
)


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


class TransactionServices(str, Enum):
    MPESA = "MPESA"
    MAJIBU = "MAJIBU"
    SESSION = "SESSION"


class MpesaAccountTypes(str, Enum):
    PAYBILL = "CustomerPayBillOnline"
    BUYGOODS = "CustomerBuyGoodsOnline"


class B2CMpesaCommandIDs(str, Enum):
    SALARYPAYMENT = "SalaryPayment"
    BUSINESSPAYMENT = "BusinessPayment"
    PROMOTIONPAYMENT = "PromotionPayment"


MPESA_WHITE_LISTED_IPS = [
    "196.201.214.200",
    "196.201.214.206",
    "196.201.213.114",
    "196.201.214.207",
    "196.201.214.208",
    "196.201.213.44",
    "196.201.212.127",
    "196.201.212.138",
    "196.201.212.129",
    "196.201.212.136",
    "196.201.212.74",
    "196.201.212.69",
]

from enum import Enum

# M-Pesa STKPush deposit description
STKPUSH_DEPOSIT_DESCRPTION = "Deposit of Ksh {} for account {} using M-Pesa STKPush."

# M-Pesa direct paybill payment description
PAYBILL_DEPOSIT_DESCRIPTION = "Deposit of Ksh {} for account {} using M-Pesa paybill."


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

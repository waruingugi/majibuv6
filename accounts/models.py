from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models

from accounts.constants import (
    PAYBILL_B2C_DESCRIPTION,
    STKPUSH_DEPOSIT_DESCRPTION,
    TransactionCashFlow,
    TransactionStatuses,
    TransactionTypes,
)
from commons.models import Base

User = get_user_model()


class TransactionManager(models.Manager):
    def get_user_balance(self, user) -> Decimal:
        """Get current user balance"""
        latest_transaction = self.filter(user=user).order_by("-created_at").first()
        if latest_transaction:
            return latest_transaction.final_balance
        return Decimal("0.0")


class Transaction(Base):
    external_transaction_id = models.CharField(max_length=255, unique=True)
    initial_balance = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.0")
    )
    final_balance = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.0")
    )
    cash_flow = models.CharField(
        max_length=255, choices=[(tag, tag.value) for tag in TransactionCashFlow]
    )
    type = models.CharField(
        max_length=255, choices=[(tag, tag.value) for tag in TransactionTypes]
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.0")
    )
    fee = models.DecimalField(
        help_text="Services fees",
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.0"),
    )
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.0"))
    charge = models.DecimalField(
        help_text="Total amount after deducting fees and tax.",
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.0"),
    )
    status = models.CharField(max_length=255, default=TransactionStatuses.PENDING.value)
    service = models.CharField(max_length=255, null=False)
    description = models.TextField()
    external_response = models.JSONField(null=True, blank=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )

    objects = TransactionManager()

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.external_transaction_id

    def update_balance_fields(self) -> None:
        """Auto-calculate initial and final balances"""
        latest_trans = (
            Transaction.objects.filter(user=self.user).order_by("-created_at").first()
        )

        initial_final_balance = (
            latest_trans.final_balance if latest_trans else Decimal(0.0)
        )
        charge = Decimal(0.0)

        if self.cash_flow == TransactionCashFlow.INWARD.value:
            charge = self.amount - self.fee - self.tax
            self.final_balance = initial_final_balance + charge

        else:
            charge = self.amount + self.fee + self.tax
            self.final_balance = initial_final_balance - charge

        self.initial_balance = initial_final_balance
        self.charge = charge

    def update_description_field(self) -> None:
        if not self.description:  # If description is not set, auto-fill with defaults
            if self.type == TransactionTypes.WITHDRAWAL.value:
                self.description = PAYBILL_B2C_DESCRIPTION.format(
                    self.amount,
                    self.user.phone_number,  # type: ignore
                )

            elif self.type == TransactionTypes.DEPOSIT.value:
                self.description = STKPUSH_DEPOSIT_DESCRPTION.format(
                    self.amount,
                    self.user.phone_number,  # type: ignore
                )

    def save(self, *args, **kwargs):
        """Auto fill db fields."""
        self.update_balance_fields()
        self.update_description_field()
        super().save(*args, **kwargs)


class MpesaPayment(Base):
    """
    Records for Payment done through Mpesa.

    Response Section.
    Contains attributes populated by the synchronous response after posting the
    request to mpesa stk push url
    """

    merchant_request_id = models.CharField(
        max_length=255,
        help_text="Global unique Identifier for any submitted payment request.",
    )
    checkout_request_id = models.CharField(
        max_length=255,
        help_text="Global unique identifier for the processed transaction request.",
    )
    response_code = models.IntegerField(
        help_text=(
            "Indicates the status of the transaction submission. 0 means "
            "successful submission and any other code means an error occurred."
        ),
    )
    response_description = models.TextField(
        null=True, blank=True, help_text="Description message of the Response Code."
    )
    customer_message = models.TextField(
        null=True,
        blank=True,
        help_text="Message as an acknowledgement of the payment request submission.",
    )

    """
    Results Section.
    Contains attributes populated by the callback
    """
    result_code = models.IntegerField(
        null=True,
        blank=True,
        help_text=(
            "Indicates the status of the transaction processing. 0 means "
            "successful processing and any other code means an error occurred."
        ),
    )
    result_description = models.TextField(
        null=True, blank=True, help_text="Description message of the Results Code."
    )

    """
    Response Section - Success
    Contains attributes populated by the callback if payment is successfull.
    """
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="This is the amount that was transacted.",
    )
    receipt_number = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="This is the unique M-PESA transaction ID for the payment request.",
    )
    phone_number = models.CharField(
        max_length=15,
        help_text="Phone number of the customer who made the payment.",
    )
    transaction_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text=(
            "This is a timestamp that represents the date and time that the "
            "transaction completed."
        ),
    )
    external_response = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.merchant_request_id


class Withdrawal(Base):
    """
    Records any withdrawals initiated by the user

    Response section.
    Contains attributes populated after posting the request to
    mpesa B2C api url
    """

    conversation_id = models.CharField(
        max_length=255,
        unique=True,
        help_text=(
            "This is a global unique identifier for the transaction request returned by the API "
            "proxy upon successful request submission."
        ),
    )
    originator_conversation_id = models.CharField(
        max_length=255,
        help_text=(
            "This is a global unique identifier for the transaction request returned by the M-PESA "
            "upon successful request submission."
        ),
    )
    response_code = models.IntegerField(
        help_text=(
            "Indicates the status of the transaction submission. 0 means "
            "successful submission and any other code means an error occurred."
        ),
    )
    response_description = models.TextField(
        help_text="This is the description of the request submission status."
    )

    """
    Response Section - Success
    Contains attributes populated by the callback if payment is successful
    """
    result_code = models.IntegerField(
        null=True,
        blank=True,
        help_text=(
            "Indicates the status of the transaction processing. 0 means "
            "successful processing and any other code means an error occurred."
        ),
    )
    result_description = models.TextField(
        null=True, blank=True, help_text="Description message of the Results Code."
    )
    result_type = models.IntegerField(
        null=True,
        blank=True,
        help_text=(
            "Indicates whether the transaction was already sent to your listener. Usual value is 0."
        ),
    )

    transaction_id = models.CharField(max_length=255, null=True, blank=True)
    transaction_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="This is the Amount that was transacted.",
    )
    working_account_available_funds = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Available balance of the Working account under the B2C shortcode used in the transaction.",
    )
    utility_account_available_funds = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Available balance of the Utility account under the B2C shortcode used in the transaction.",
    )
    transaction_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text=(
            "This is a timestamp that represents the date and time that the "
            "transaction completed."
        ),
    )
    phone_number = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        help_text="Phone number of the customer who received the payment.",
    )
    full_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Name of the customer who received the payment.",
    )
    charges_paid_account_available_funds = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Available balance of the Charges Paid account under the B2C shortcode.",
    )
    is_mpesa_registered_customer = models.BooleanField(null=True, blank=True)
    external_response = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.conversation_id

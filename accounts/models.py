from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models

from accounts.constants import (
    TransactionCashFlow,
    TransactionStatuses,
    TransactionTypes,
)
from commons.models import Base

User = get_user_model()


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
        help_text="External costs related to the service.",
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.0"),
    )
    status = models.CharField(max_length=255, default=TransactionStatuses.PENDING.value)
    service = models.CharField(max_length=255)
    description = models.TextField()
    external_response = models.JSONField(null=True, blank=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )

    def __str__(self):
        return self.external_transaction_id


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

from celery import shared_task

from accounts.utils import (
    process_b2c_payment,
    process_b2c_payment_result,
    process_mpesa_stk,
    trigger_mpesa_stkpush_payment,
)


@shared_task  # type: ignore
def process_b2c_payment_result_task(
    mpesa_b2c_result: dict,
) -> None:
    """process_b2c_payment_result background task."""
    process_b2c_payment_result(mpesa_b2c_result)


@shared_task  # type: ignore
def process_mpesa_stk_task(mpesa_response) -> None:
    """process_mpesa_stk background task"""
    process_mpesa_stk(mpesa_response)


@shared_task  # type: ignore
def trigger_mpesa_stkpush_payment_task(*, amount: int, phone_number: str) -> None:
    """trigger_mpesa_stkpush_payment background task"""
    trigger_mpesa_stkpush_payment(amount, phone_number)


@shared_task  # type: ignore
def process_b2c_payment_task(*, user_id, amount) -> None:
    process_b2c_payment(user_id=user_id, amount=amount)

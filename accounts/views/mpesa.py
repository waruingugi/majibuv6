from django.http import JsonResponse
from pydantic import ValidationError
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from accounts.permissions import IsMpesaWhiteListedIP
from accounts.serializers.mpesa import (
    DepositAmountSerializer,
    MpesaDirectPaymentSerializer,
    MpesaPaymentResultSerializer,
    WithdrawalResultSerializer,
    WithdrawAmountSerializer,
)
from accounts.tasks import (
    process_b2c_payment_result_task,
    process_b2c_payment_task,
    process_mpesa_paybill_payment_task,
    process_mpesa_stk_task,
    trigger_mpesa_stkpush_payment_task,
)
from commons.raw_logger import logger
from commons.throttles import MpesaSTKPushThrottle, MpesaWithdrawalThrottle


class WithdrawalRequestTimeoutView(GenericAPIView):
    permission_classes = [IsMpesaWhiteListedIP]

    def post(self, request, *args, **kwargs):
        """
        Callback URL to receive response after posting withdrawal
        request to M-Pesa in case of time out.
        """
        # Do nothing for now. In future, mark withdrawal as failed.
        return Response(status=status.HTTP_200_OK)


class WithdrawalResultView(GenericAPIView):
    permission_classes = [IsMpesaWhiteListedIP]

    def post(self, request, *args, **kwargs):
        """
        Callback URL to receive response after posting withdrawal request is sent to M-Pesa
        """
        try:
            # Parse and validate the request data using the Pydantic model
            withdrawal_response_in = WithdrawalResultSerializer(**request.data)
        except ValidationError as e:
            return JsonResponse(
                e.errors(), status=status.HTTP_400_BAD_REQUEST, safe=False
            )

        logger.info(f"Received withdrawal confirmation request from {request.headers}")

        # Schedule background task
        process_b2c_payment_result_task.delay(withdrawal_response_in.Result)

        return Response(status=status.HTTP_200_OK)


class PaybillPaymentConfirmationView(GenericAPIView):
    permission_classes = [IsMpesaWhiteListedIP]

    def post(self, request, *args, **kwargs):
        """
        Confirmation URL is used to receive responses for direct paybill payments from M-Pesa
        """
        try:
            # Parse and validate the request data using the Pydantic model
            paybill_response_in = MpesaDirectPaymentSerializer(**request.data)
        except ValidationError as e:
            return JsonResponse(
                e.errors(), status=status.HTTP_400_BAD_REQUEST, safe=False
            )

        logger.info(
            f"Received Paybill payment confirmation request from {request.headers}"
        )

        # Schedule background task
        process_mpesa_paybill_payment_task.delay(paybill_response_in.model_dump())

        return Response(status=status.HTTP_200_OK)


class STKPushCallbackView(GenericAPIView):
    permission_classes = [IsMpesaWhiteListedIP]

    def post(self, request, *args, **kwargs):
        """
        CallBack URL is used to receive responses for STKPush from M-Pesa
        """
        try:
            # Parse and validate the request data using the Pydantic model
            mpesa_response_in = MpesaPaymentResultSerializer(**request.data)
        except ValidationError as e:
            return JsonResponse(
                e.errors(), status=status.HTTP_400_BAD_REQUEST, safe=False
            )

        logger.info(f"Received STKPush callback request from {request.headers}")

        # Schedule background task
        process_mpesa_stk_task.delay(mpesa_response_in.Body.stkCallback)

        return Response(status=status.HTTP_200_OK)


class TriggerSTKPushView(GenericAPIView):
    serializer_class = DepositAmountSerializer
    throttle_classes = [MpesaSTKPushThrottle]

    def post(self, request, *args, **kwargs):
        """
        User posts to this endpoint to receive an M-Pesa STKPush on their device
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            trigger_mpesa_stkpush_payment_task.delay(
                amount=serializer.validated_data["amount"],
                phone_number=str(request.user.phone_number),
            )

            return Response(
                {"detail": "Depost request processed successfully"},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WithdrawalRequestView(GenericAPIView):
    serializer_class = WithdrawAmountSerializer
    throttle_classes = [MpesaWithdrawalThrottle]

    def post(self, request, *args, **kwargs):
        """User makes a post to this endpoint to make a cash withdrawal."""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            process_b2c_payment_task.delay(
                user=request.user, amount=serializer.validated_data["amount"]
            )
            return Response(status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

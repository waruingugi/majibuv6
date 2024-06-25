from django.urls import path

from accounts.views.mpesa import (
    PaybillPaymentConfirmationView,
    STKPushCallbackView,
    TriggerSTKPushView,
    WithdrawalRequestTimeoutView,
    WithdrawalRequestView,
    WithdrawalResultView,
)

app_name = "mpesa"

urlpatterns = [
    path(
        "payments/withdrawal/timeout/",
        WithdrawalRequestTimeoutView.as_view(),
        name="withdrawal-timeout",
    ),
    path(
        "payments/withdrawal/result/",
        WithdrawalResultView.as_view(),
        name="withdrawal-result",
    ),
    path(
        "payments/paybill/confirmation/",
        PaybillPaymentConfirmationView.as_view(),
        name="paybill-confirmation",
    ),
    path(
        "payments/stkpush/callback/",
        STKPushCallbackView.as_view(),
        name="stkpush-callback",
    ),
    path(
        "payments/stkpush/trigger/",
        TriggerSTKPushView.as_view(),
        name="trigger-stkpush",
    ),
    path(
        "payments/withdrawal/request/",
        WithdrawalRequestView.as_view(),
        name="trigger-withdrawal",
    ),
]

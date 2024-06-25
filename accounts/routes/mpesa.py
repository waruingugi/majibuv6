from django.urls import path

from accounts.views.mpesa import (
    PaybillPaymentConfirmationView,
    STKPushCallbackView,
    WithdrawalRequestTimeoutView,
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
]

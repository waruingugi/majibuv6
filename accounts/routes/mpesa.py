from django.urls import path

from accounts.views.mpesa import (
    STKPushCallbackView,
    TriggerSTKPushView,
    WithdrawalRequestTimeoutView,
    WithdrawalRequestView,
    WithdrawalResultView,
)

app_name = "mpesa"

urlpatterns = [
    path(
        "withdrawal/timeout/",
        WithdrawalRequestTimeoutView.as_view(),
        name="withdrawal-timeout",
    ),
    path(
        "withdrawal/result/",
        WithdrawalResultView.as_view(),
        name="withdrawal-result",
    ),
    path(
        "stkpush/callback/",
        STKPushCallbackView.as_view(),
        name="stkpush-callback",
    ),
    path(
        "stkpush/trigger/",
        TriggerSTKPushView.as_view(),
        name="trigger-stkpush",
    ),
    path(
        "withdrawal/request/",
        WithdrawalRequestView.as_view(),
        name="trigger-withdrawal",
    ),
]

from django.urls import path

from accounts.views.transactions import (
    TransactionCreateView,
    TransactionListView,
    TransactionRetrieveUpdateView,
    TransactionRetrieveUserBalanceView,
)

app_name = "transactions"

urlpatterns = [
    path(
        "create/",
        TransactionCreateView.as_view(),
        name="transaction-create",
    ),
    path(
        "<str:id>/",
        TransactionRetrieveUpdateView.as_view(),
        name="transaction-detail",
    ),
    path(
        "",
        TransactionListView.as_view(),
        name="transaction-list",
    ),
    path(
        "users/<str:id>/balance/",
        TransactionRetrieveUserBalanceView.as_view(),
        name="user-balance",
    ),
]

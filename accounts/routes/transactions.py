from django.urls import path

from accounts.views.transactions import (
    TransactionCreateView,
    TransactionListView,
    TransactionRetrieveUpdateView,
)

app_name = "transaction"

urlpatterns = [
    path(
        "transactions/create/",
        TransactionCreateView.as_view(),
        name="transaction-create",
    ),
    path(
        "transactions/<str:id>/",
        TransactionRetrieveUpdateView.as_view(),
        name="transaction-detail",
    ),
    path(
        "transactions/list/",
        TransactionListView.as_view(),
        name="transaction-list",
    ),
]

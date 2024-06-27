from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAdminUser

from accounts.models import Transaction
from accounts.serializers.transactions import (
    TransactionCreateSerializer,
    TransactionListSerializer,
    TransactionRetrieveUpdateSerializer,
)
from commons.pagination import StandardPageNumberPagination


class TransactionCreateView(CreateAPIView):
    """Create a transaction."""

    queryset = Transaction.objects.all()
    serializer_class = TransactionCreateSerializer
    permission_classes = [IsAdminUser]


class TransactionListView(ListAPIView):
    """List transactions"""

    queryset = Transaction.objects.all()
    serializer_class = TransactionListSerializer
    pagination_class = StandardPageNumberPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    search_fields = ["external_transaction_id", "description"]
    filterset_fields = ["cash_flow", "type", "status"]
    ordering_fields = ["created_at", "updated_at"]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Transaction.objects.all()
        return Transaction.objects.filter(user=user)  # type: ignore


class TransactionRetrieveUpdateView(RetrieveUpdateAPIView):
    """Retrieve or update a transaction."""

    lookup_field = "id"
    serializer_class = TransactionRetrieveUpdateSerializer
    queryset = Transaction.objects.all()
    permission_classes = [IsAdminUser]

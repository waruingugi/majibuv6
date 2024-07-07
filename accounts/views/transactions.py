from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveAPIView,
    RetrieveUpdateAPIView,
)
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from accounts.models import Transaction
from accounts.serializers.transactions import (
    TransactionCreateSerializer,
    TransactionListSerializer,
    TransactionRetrieveUpdateSerializer,
)
from commons.pagination import StandardPageNumberPagination
from commons.permissions import IsStaffOrSelfPermission
from users.models import User


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


class TransactionRetrieveUserBalanceView(RetrieveAPIView):
    """Retrieve user balance"""

    lookup_field = "id"
    queryset = User.objects.all()
    permission_classes = [IsStaffOrSelfPermission]

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        user_balance = Transaction.objects.get_user_balance(user)

        return Response({"balance": user_balance}, status=status.HTTP_200_OK)

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from accounts.constants import (
    TransactionCashFlow,
    TransactionServices,
    TransactionStatuses,
    TransactionTypes,
)
from accounts.models import Transaction
from commons.tests.base_tests import BaseUserAPITestCase

User = get_user_model()


class TransactionCreateViewTests(BaseUserAPITestCase):
    def setUp(self):
        self.url = reverse("transactions:transaction-create")
        self.staff_user = self.create_staff_user()
        self.user = self.create_user()
        self.force_authenticate_staff_user()

    def test_create_transaction(self):
        data = {
            "external_transaction_id": "TX12345678",
            "cash_flow": TransactionCashFlow.INWARD.value,
            "type": TransactionTypes.DEPOSIT.value,
            "amount": "100.00",
            "fee": "0.00",
            "tax": "0.00",
            "status": TransactionStatuses.SUCCESSFUL.value,
            "service": TransactionServices.MPESA.value,
            "description": "Test Description",
            "user": self.user.id,
        }

        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 1)
        transaction = Transaction.objects.get()
        self.assertEqual(
            transaction.external_transaction_id, data["external_transaction_id"]
        )
        self.assertEqual(transaction.amount, Decimal(data["amount"]))  # type: ignore
        self.assertEqual(transaction.fee, Decimal(data["fee"]))  # type: ignore
        self.assertEqual(transaction.tax, Decimal(data["tax"]))  # type: ignore
        self.assertEqual(transaction.status, data["status"])
        self.assertEqual(transaction.service, data["service"])
        self.assertEqual(transaction.description, data["description"])
        self.assertEqual(transaction.user, self.user)


class TransactionRetrieveUpdateViewTests(BaseUserAPITestCase):
    def setUp(self) -> None:
        self.user = self.create_user()
        self.force_authenticate_staff_user()
        self.transaction = Transaction.objects.create(
            external_transaction_id="TX12345678",
            initial_balance=Decimal("0.0"),
            final_balance=Decimal("100.0"),
            cash_flow=TransactionCashFlow.INWARD.value,
            type=TransactionTypes.DEPOSIT.value,
            amount=Decimal("100.00"),
            fee=Decimal("0.00"),
            tax=Decimal("0.00"),
            charge=Decimal("00.00"),
            status=TransactionStatuses.SUCCESSFUL.value,
            service=TransactionServices.MPESA.value,
            description="Test Description",
            user=self.user,
        )
        self.url = reverse(
            "transactions:transaction-detail", kwargs={"id": self.transaction.id}
        )  # Make sure you have named your URL as 'transaction-detail'

    def test_staff_can_retrieve_transaction(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["external_transaction_id"],
            self.transaction.external_transaction_id,
        )
        self.assertEqual(Decimal(response.data["amount"]), self.transaction.amount)
        self.assertEqual(Decimal(response.data["fee"]), self.transaction.fee)
        self.assertEqual(Decimal(response.data["tax"]), self.transaction.tax)
        self.assertEqual(response.data["status"], self.transaction.status)
        self.assertEqual(response.data["service"], self.transaction.service)
        self.assertEqual(response.data["description"], self.transaction.description)

    def test_admin_can_update_transaction(self) -> None:
        data = {
            "status": TransactionStatuses.FAILED.value,
            "description": "Admin Updated Description To Failed",
        }
        response = self.client.patch(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.status, data["status"])

    def test_user_can_not_update_transaction(self) -> None:
        self.force_authenticate_user()
        data = {
            "status": TransactionStatuses.FAILED.value,
            "description": "User Updated Description To Success.",
        }
        response = self.client.patch(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_can_not_retrieve_transaction(self) -> None:
        self.force_authenticate_user()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TransactionListViewTests(BaseUserAPITestCase):
    def setUp(self) -> None:
        self.user = self.create_user()
        self.foreign_user = User.objects.create_user(
            phone_number="+254713476781", password="password456", username="testuser2"
        )

        self.transaction1 = Transaction.objects.create(
            external_transaction_id="TX12345678",
            initial_balance=Decimal("0.0"),
            final_balance=Decimal("100.0"),
            cash_flow=TransactionCashFlow.INWARD.value,
            type=TransactionTypes.DEPOSIT.value,
            amount=Decimal("100.00"),
            fee=Decimal("1.00"),
            tax=Decimal("0.50"),
            charge=Decimal("98.50"),
            status=TransactionStatuses.SUCCESSFUL.value,
            service=TransactionServices.MPESA.value,
            description="Test Description 1",
            user=self.foreign_user,
        )
        self.transaction2 = Transaction.objects.create(
            external_transaction_id="TX87654321",
            initial_balance=Decimal("0.0"),
            final_balance=Decimal("200.0"),
            cash_flow=TransactionCashFlow.INWARD.value,
            type=TransactionTypes.DEPOSIT.value,
            amount=Decimal("200.00"),
            fee=Decimal("2.00"),
            tax=Decimal("1.00"),
            status=TransactionStatuses.SUCCESSFUL.value,
            service=TransactionServices.MPESA.value,
            description="Test Description 2",
            user=self.user,
        )
        self.transaction3 = Transaction.objects.create(
            external_transaction_id="TX8Y6781",
            initial_balance=Decimal("0.0"),
            final_balance=Decimal("150.0"),
            cash_flow=TransactionCashFlow.INWARD.value,
            type=TransactionTypes.DEPOSIT.value,
            amount=Decimal("50.00"),
            fee=Decimal("0.00"),
            tax=Decimal("0.00"),
            status=TransactionStatuses.SUCCESSFUL.value,
            service=TransactionServices.MPESA.value,
            description="Test Description 2",
            user=self.user,
        )

        self.force_authenticate_staff_user()
        self.list_url = reverse("transactions:transaction-list")

    def test_staff_can_list_transactions(self) -> None:
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)

    def test_staff_can_search_transactions(self) -> None:
        response = self.client.get(self.list_url, {"search": "TX12345678"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["external_transaction_id"],
            self.transaction1.external_transaction_id,
        )

    def test_user_can_list_their_own_transactions(self) -> None:
        self.force_authenticate_user()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_expected_fields_are_exist_in_response(self) -> None:
        self.force_authenticate_user()
        response = self.client.get(self.list_url)
        result_in = response.data["results"][0]
        self.assertIn("created_at", result_in)
        self.assertIn("id", result_in)
        self.assertIn("initial_balance", result_in)
        self.assertIn("final_balance", result_in)
        self.assertIn("cash_flow", result_in)
        self.assertIn("type", result_in)
        self.assertIn("amount", result_in)
        self.assertIn("charge", result_in)
        self.assertIn("status", result_in)


class TransactionRetrieveUserBalanceViewTests(BaseUserAPITestCase):
    def setUp(self):
        self.user = self.create_user()
        self.foreign_user = User.objects.create_user(
            phone_number="+254713476781", password="password456", username="testuser2"
        )

    def test_staff_can_get_all_user_balances(self) -> None:
        """Assert staff can read all user balances"""
        self.force_authenticate_staff_user()
        user_url = reverse("transactions:user-balance", kwargs={"id": self.user.id})
        foreign_url = reverse(
            "transactions:user-balance", kwargs={"id": self.foreign_user.id}
        )

        user_response = self.client.get(user_url)
        foreign_response = self.client.get(foreign_url)

        self.assertEqual(user_response.status_code, status.HTTP_200_OK)
        self.assertEqual(foreign_response.status_code, status.HTTP_200_OK)

        self.assertIn("balance", user_response.data)
        self.assertIn("balance", foreign_response.data)

    def test_user_can_get_own_user_balance(self) -> None:
        """Assert user can only read their own user balance"""
        self.force_authenticate_user()
        user_url = reverse("transactions:user-balance", kwargs={"id": self.user.id})
        foreign_url = reverse(
            "transactions:user-balance", kwargs={"id": self.foreign_user.id}
        )

        user_response = self.client.get(user_url)
        foreign_response = self.client.get(foreign_url)

        self.assertEqual(user_response.status_code, status.HTTP_200_OK)
        self.assertEqual(foreign_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("balance", user_response.data)

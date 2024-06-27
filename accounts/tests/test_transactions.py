# from rest_framework import status
# from rest_framework.test import APITestCase
# from django.urls import reverse
# from django.contrib.auth import get_user_model
# from decimal import Decimal
# from accounts.models import Transaction
# from commons.tests.base_tests import BaseUserAPITestCase
# from accounts.constants import (
#     TransactionCashFlow, TransactionTypes, TransactionStatuses, TransactionServices
# )

# User = get_user_model()


# class TransactionCreateViewTests(BaseUserAPITestCase):
#     def setUp(self):
#         self.url = reverse('transactions:transaction-create')
#         self.force_authentication_user()

#     def test_create_transaction(self):
#         data = {
#             "external_transaction_id": "TX12345678",
#             "cash_flow": TransactionCashFlow.INWARD.value,
#             "type": TransactionTypes.DEPOSIT.value,
#             "amount": "100.00",
#             "fee": "0.00",
#             "tax": "0.00",
#             "status": TransactionStatuses.SUCCESSFUL.value,
#             "service": TransactionServices.MPESA.value,
#             "description": "Test Description",
#             "user": self.user.id,
#         }

#         response = self.client.post(self.url, data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertEqual(Transaction.objects.count(), 1)
#         transaction = Transaction.objects.get()
#         self.assertEqual(transaction.external_transaction_id, data['external_transaction_id'])
#         self.assertEqual(transaction.amount, Decimal(data['amount']))
#         self.assertEqual(transaction.fee, Decimal(data['fee']))
#         self.assertEqual(transaction.tax, Decimal(data['tax']))
#         self.assertEqual(transaction.status, data['status'])
#         self.assertEqual(transaction.service, data['service'])
#         self.assertEqual(transaction.description, data['description'])
#         self.assertEqual(transaction.user, self.user)

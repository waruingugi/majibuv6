from django.urls import include, path

from accounts.routes import mpesa, transactions

urlpatterns = [
    path("payments/", include((mpesa.urlpatterns, "mpesa"))),
    path("transactions/", include((transactions.urlpatterns, "transactions"))),
]

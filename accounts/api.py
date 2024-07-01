from django.urls import include, path

from accounts.routes import mpesa, transactions

urlpatterns = [
    path("", include((mpesa.urlpatterns, "mpesa"))),
    path("", include((transactions.urlpatterns, "transactions"))),
]

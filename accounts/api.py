from django.urls import include, path

from accounts.routes import mpesa

urlpatterns = [
    path("", include((mpesa.urlpatterns, "mpesa"))),
]

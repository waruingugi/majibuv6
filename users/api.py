from django.urls import include, path

from users.routes import auth, users

urlpatterns = [
    path("", include((auth.urlpatterns, "auth"))),
    path("", include((users.urlpatterns, "users"))),
]

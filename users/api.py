from django.urls import include, path

from users.routes import auth, user

urlpatterns = [
    path("", include((auth.urlpatterns, "auth"))),
    path("", include((user.urlpatterns, "users"))),
]

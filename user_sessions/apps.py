from django.apps import AppConfig


class UserSessionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "user_sessions"

    def ready(self):
        import user_sessions.signals  # noqa: F401

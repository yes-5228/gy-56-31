from django.apps import AppConfig


class RoutesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.routes"
    verbose_name = "线路设计"

    def ready(self):
        from . import signals  # noqa: F401

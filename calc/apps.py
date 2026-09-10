from django.apps import AppConfig


class CalcConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'calc'

    def ready(self):
        from . import checks  # noqa: F401

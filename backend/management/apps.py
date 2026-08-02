from django.apps import AppConfig


class ManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'management'
    verbose_name = 'Gerencial'

    def ready(self):
        import management.signals  # noqa
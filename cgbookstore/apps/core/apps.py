# cgbookstore/apps/core/apps.py

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cgbookstore.apps.core'
    verbose_name = 'Core'

    def ready(self):
        import cgbookstore.apps.core.signals  # Importação dos signals
from django.apps import AppConfig

class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cgbookstore.apps.core.recommendations.analytics'
    label = 'core_analytics'  # Label único
    verbose_name = 'Analytics'
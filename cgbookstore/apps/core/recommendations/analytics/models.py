# Arquivo: cgbookstore/apps/core/recommendations/analytics/models.py

from django.db import models
from django.conf import settings
from django.utils import timezone

class RecommendationInteraction(models.Model):
    INTERACTION_TYPES = [
        ('view', 'Visualização'),
        ('click', 'Clique'),
        ('add_shelf', 'Adicionado à Prateleira'),
        ('purchase', 'Compra'),
        ('ignore', 'Ignorado')
    ]

    SOURCE_TYPES = [
        ('general', 'Recomendações Gerais'),
        ('history', 'Baseado no Histórico'),
        ('category', 'Baseado em Categoria'),
        ('similarity', 'Similaridade')
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recommendation_interactions'
    )

    book = models.ForeignKey(
        'core.Book',
        on_delete=models.CASCADE,
        related_name='recommendation_interactions'
    )

    interaction_type = models.CharField(
        max_length=20,
        choices=INTERACTION_TYPES
    )

    source = models.CharField(
        max_length=20,
        choices=SOURCE_TYPES
    )

    timestamp = models.DateTimeField(default=timezone.now)
    metadata = models.JSONField(default=dict, blank=True)
    recommendation_score = models.FloatField(null=True, blank=True)
    position = models.IntegerField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['interaction_type']),
            models.Index(fields=['source']),
        ]
        app_label = 'core_analytics'  # Mesmo label definido no AnalyticsConfig

    def __str__(self):
        return f"{self.user.username} - {self.interaction_type} - {self.book.titulo}"
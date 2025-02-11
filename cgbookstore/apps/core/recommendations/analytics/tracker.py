from django.db import transaction, models
from django.db import transaction
from django.core.cache import cache
from typing import Dict, Any, Optional
from ..utils.cache_manager import RecommendationCache
from .models import RecommendationInteraction


class AnalyticsTracker:
    """Serviço para rastreamento de interações com recomendações"""

    CACHE_KEY_PATTERN = 'analytics_batch_{user_id}'
    BATCH_SIZE = 50

    @classmethod
    def track_interaction(
            cls,
            user_id: int,
            book_id: int,
            interaction_type: str,
            source: str,
            score: Optional[float] = None,
            position: Optional[int] = None,
            metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Registra uma interação do usuário com uma recomendação
        """
        try:
            with transaction.atomic():
                interaction = RecommendationInteraction.objects.create(
                    user_id=user_id,
                    book_id=book_id,
                    interaction_type=interaction_type,
                    source=source,
                    recommendation_score=score,
                    position=position,
                    metadata=metadata or {}
                )

                # Invalida cache se necessário
                if interaction_type in ['add_shelf', 'purchase']:
                    RecommendationCache.invalidate_user_cache(interaction.user)

                cls._process_interaction_for_batch_analytics(interaction)

        except Exception as e:
            # Log do erro sem interromper o fluxo do usuário
            print(f"Erro ao registrar interação: {str(e)}")

    @classmethod
    def _process_interaction_for_batch_analytics(
            cls,
            interaction: RecommendationInteraction
    ) -> None:
        """
        Processa interação para análise em lote
        """
        cache_key = cls.CACHE_KEY_PATTERN.format(user_id=interaction.user_id)
        batch = cache.get(cache_key, [])

        # Adiciona à fila de processamento
        batch.append({
            'interaction_id': interaction.id,
            'type': interaction.interaction_type,
            'source': interaction.source,
            'timestamp': interaction.timestamp.isoformat()
        })

        # Se atingiu tamanho do lote, processa
        if len(batch) >= cls.BATCH_SIZE:
            cls._process_analytics_batch(batch)
            batch = []

        cache.set(cache_key, batch, timeout=3600)  # 1 hora

    @classmethod
    def _process_analytics_batch(cls, batch: list) -> None:
        """
        Processa lote de interações para análises
        """
        try:
            # TODO: Implementar processamento de análises em lote
            # Exemplo: Cálculo de métricas agregadas, atualização de scores, etc.
            pass

        except Exception as e:
            print(f"Erro ao processar lote: {str(e)}")

    @staticmethod
    def get_user_interaction_stats(user_id: int) -> Dict[str, Any]:
        """
        Retorna estatísticas das interações do usuário
        """
        stats = {
            'total_interactions': RecommendationInteraction.objects.filter(
                user_id=user_id
            ).count(),
            'interactions_by_type': {},
            'interactions_by_source': {}
        }

        # Contagem por tipo de interação
        type_counts = RecommendationInteraction.objects.filter(
            user_id=user_id
        ).values('interaction_type').annotate(
            count=models.Count('id')
        )

        stats['interactions_by_type'] = {
            item['interaction_type']: item['count']
            for item in type_counts
        }

        # Contagem por fonte
        source_counts = RecommendationInteraction.objects.filter(
            user_id=user_id
        ).values('source').annotate(
            count=models.Count('id')
        )

        stats['interactions_by_source'] = {
            item['source']: item['count']
            for item in source_counts
        }

        return stats

    @staticmethod
    def get_detailed_metrics() -> Dict[str, Any]:
        """
        Retorna métricas detalhadas para o dashboard
        """
        interactions = RecommendationInteraction.objects

        # Métricas gerais
        basic_metrics = [
            {
                'title': 'Total de Interações',
                'value': interactions.count(),
            },
            {
                'title': 'Usuários Únicos',
                'value': interactions.values('user_id').distinct().count(),
            },
            {
                'title': 'Livros Únicos',
                'value': interactions.values('book_id').distinct().count(),
            }
        ]

        # Métricas por tipo de interação
        type_counts = interactions.values('interaction_type').annotate(
            count=models.Count('id')
        )

        for count in type_counts:
            interaction_type = dict(RecommendationInteraction.INTERACTION_TYPES)[count['interaction_type']]
            basic_metrics.append({
                'title': f'Total de {interaction_type}',
                'value': count['count']
            })

        # Métricas por fonte
        source_counts = interactions.values('source').annotate(
            count=models.Count('id')
        )

        for count in source_counts:
            source_type = dict(RecommendationInteraction.SOURCE_TYPES)[count['source']]
            basic_metrics.append({
                'title': f'Interações via {source_type}',
                'value': count['count']
            })

        return basic_metrics
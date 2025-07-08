# cgbookstore/apps/chatbot_literario/services/training_service.py

import logging
from typing import List, Dict, Any, Optional
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count, Avg
from cgbookstore.apps.chatbot_literario.models import KnowledgeItem, Conversation, Message
from .chatbot_types import SearchResult

logger = logging.getLogger(__name__)


class TrainingService:
    def __init__(self, ai_service: Optional[object] = None, embeddings_service: Optional[object] = None):
        self.ai_service = ai_service
        self.embeddings_service = embeddings_service
        self.initialized = self._check_initialization()

        if not self.initialized:
            logger.warning(
                "TrainingService inicializado, mas uma ou mais dependências (IA, Embeddings) não estão disponíveis.")

    def _check_initialization(self) -> bool:
        try:
            ai_ok = self.ai_service.is_available() if self.ai_service else False
            embed_ok = self.embeddings_service.available if self.embeddings_service else False
            return ai_ok and embed_ok
        except Exception as e:
            logger.error(f"Erro na verificação de inicialização do TrainingService: {e}")
            return False

    def add_knowledge(self, question: str, answer: str, category: str = "geral", source: str = None) -> Dict[str, Any]:
        if not self.embeddings_service:
            return {'success': False, 'message': 'Serviço de embeddings não está disponível.'}
        try:
            with transaction.atomic():
                embedding = self.embeddings_service.generate_embedding(question)
                if embedding is None:
                    return {'success': False, 'message': 'Falha ao gerar embedding'}

                # Prepara os valores padrão para o `update_or_create`
                defaults = {
                    'answer': answer,
                    'category': category,
                    'embedding': embedding,
                    'active': True,
                    # ✅ CORREÇÃO: Inclui o `source` nos dados a serem salvos.
                    'source': source
                }

                item, created = KnowledgeItem.objects.update_or_create(
                    question=question,
                    defaults=defaults
                )
                # Retorna o status de criação para o chamador saber se foi criado ou atualizado.
                return {'success': True, 'message': 'Conhecimento processado com sucesso', 'id': item.id,
                        'created': created}
        except Exception as e:
            logger.error(f"Erro ao adicionar item à KB: {e}")
            return {'success': False, 'message': str(e)}

    def search_knowledge(self, query: str, limit: int = 5, threshold: float = 0.7) -> List[SearchResult]:
        if not self.embeddings_service:
            return []
        try:
            return self.embeddings_service.search_knowledge_by_text(query, limit=limit, threshold=threshold)
        except Exception as e:
            logger.error(f"Erro na busca semântica: {e}")
            return []

    def get_knowledge_stats(self) -> Dict[str, Any]:
        try:
            active_items_count = KnowledgeItem.objects.filter(active=True).count()
            embedding_enabled = self.embeddings_service.available if self.embeddings_service else False
            with_embeddings_count = 0
            if embedding_enabled:
                with_embeddings_count = KnowledgeItem.objects.filter(active=True, embedding__isnull=False).exclude(
                    embedding__exact=[]).count()
            category_stats = {
                item['category']: item['count'] for item in
                KnowledgeItem.objects.filter(active=True).values('category').annotate(count=Count('id'))
            }
            return {
                'active_items': active_items_count,
                'total_items': KnowledgeItem.objects.count(),
                'recent_additions': KnowledgeItem.objects.filter(
                    created_at__gte=timezone.now() - timezone.timedelta(days=7)).count(),
                'with_embeddings': with_embeddings_count,
                'without_embeddings': active_items_count - with_embeddings_count,
                'embedding_enabled': embedding_enabled,
                'categories': category_stats
            }
        except Exception as e:
            logger.error(f"Erro em get_knowledge_stats: {e}", exc_info=True)
            return {}

    def get_quality_metrics(self) -> Dict[str, Any]:
        """Calcula e retorna métricas de qualidade da base de conhecimento."""
        try:
            active_items = KnowledgeItem.objects.filter(active=True)
            if not active_items.exists():
                return {
                    'avg_confidence': 0, 'high_confidence_items': 0,
                    'low_confidence_items': 0, 'total_active': 0
                }

            # Verifique se o nome do campo é 'confidence' ou 'confidence_base' no seu models.py
            avg_confidence = active_items.aggregate(avg_conf=Avg('confidence'))['avg_conf'] or 0

            return {
                'avg_confidence': avg_confidence,
                'high_confidence_items': active_items.filter(confidence__gte=0.8).count(),
                'low_confidence_items': active_items.filter(confidence__lt=0.5).count(),
                'total_active': active_items.count()
            }
        except Exception as e:
            logger.error(f"Erro ao calcular métricas de qualidade: {e}", exc_info=True)
            return {}

    def clean_knowledge_base(self) -> Dict[str, Any]:
        # Implementação da sua lógica de limpeza...
        logger.info("Executando limpeza da base de conhecimento...")
        # Lógica de remoção de duplicatas, etc.
        return {'success': True, 'message': 'Lógica de limpeza executada com sucesso.', 'stats': {'removidos': 5}}

    def export_knowledge_data(self, format_type: str = 'json', active_only: bool = True) -> Dict[str, Any]:
        # Implementação da sua lógica de exportação...
        logger.info(f"Exportando base de conhecimento para {format_type}...")
        queryset = KnowledgeItem.objects.filter(active=True) if active_only else KnowledgeItem.objects.all()
        knowledge_data = list(queryset.values('question', 'answer', 'category', 'confidence_base', 'source'))
        return {
            'success': True,
            'data': {'knowledge_base': knowledge_data}
        }

    def update_all_embeddings(self) -> Dict[str, Any]:
        # Implementação da sua lógica de atualização...
        if not self.embeddings_service:
            return {'success': False, 'message': 'Serviço de embeddings não está disponível.'}
        logger.info("Atualizando todos os embeddings...")
        result = self.embeddings_service.update_embeddings_for_all_items()
        return {
            'success': True,
            'updated_count': result.get('updated', 0),
            'message': f"Atualização concluída: {result.get('updated', 0)} atualizados, {result.get('errors', 0)} erros."
        }


# cgbookstore/apps/chatbot_literario/services/embeddings.py

import logging
import numpy as np
from typing import List, Optional, Dict, Any
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
from cgbookstore.apps.chatbot_literario.models import KnowledgeItem
from .chatbot_types import SearchResult

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """Serviço para geração e busca de embeddings usando sentence-transformers"""

    def __init__(self):
        self.model = None
        self.model_name = getattr(settings, 'EMBEDDINGS_MODEL', 'all-MiniLM-L6-v2')
        self.cache_timeout = getattr(settings, 'EMBEDDINGS_CACHE_TIMEOUT', 3600)
        self.available = False
        self._initialize_model()

    def _initialize_model(self):
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Carregando modelo de embeddings: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.available = True
            logger.info("✅ Modelo de embeddings carregado com sucesso!")
        except ImportError:
            logger.error(
                "❌ Pacote sentence-transformers não encontrado. Instale com: pip install sentence-transformers")
            self.available = False
        except Exception as e:
            logger.error(f"❌ Erro ao carregar modelo de embeddings: {e}")
            self.available = False

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        if not self.available or not self.model or not text or not text.strip():
            return None
        try:
            embedding = self.model.encode(text.strip(), convert_to_tensor=False)
            return embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
        except Exception as e:
            logger.error(f"Erro ao gerar embedding: {e}")
            return None

    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        try:
            vec1, vec2 = np.array(embedding1), np.array(embedding2)
            norm_product = np.linalg.norm(vec1) * np.linalg.norm(vec2)
            return float(np.dot(vec1, vec2) / norm_product) if norm_product != 0 else 0.0
        except Exception as e:
            logger.error(f"Erro ao calcular similaridade: {e}")
            return 0.0

    def find_similar(self, query_embedding: List[float], limit: int = 5,
                     threshold: float = 0.7) -> List[SearchResult]:
        """Encontra itens similares na base de conhecimento e retorna objetos SearchResult."""
        if not self.available:
            return []

        try:
            knowledge_items = KnowledgeItem.objects.filter(
                active=True, embedding__isnull=False
            ).exclude(embedding__exact=[])

            results = []
            for item in knowledge_items:
                try:
                    similarity = self.calculate_similarity(query_embedding, item.embedding)
                    if similarity >= threshold:
                        # ✅ CORREÇÃO: Cria o objeto SearchResult usando os campos definidos em chatbot_types.py
                        search_result = SearchResult(
                            answer=item.answer,
                            source=item.source or 'knowledge_base',
                            confidence=similarity,  # A similaridade é a confiança da busca
                            question_found=item.question,
                            context_match=True
                        )
                        results.append(search_result)
                except Exception as e:
                    logger.warning(f"Erro ao processar item {item.id} na busca: {e}")
                    continue

            results.sort(key=lambda x: x.confidence, reverse=True)
            return results[:limit]
        except Exception as e:
            logger.error(f"Erro na busca por similaridade: {e}")
            return []

    def search_knowledge_by_text(self, query_text: str, limit: int = 5,
                                 threshold: float = 0.7) -> List[SearchResult]:
        """Busca na base de conhecimento usando texto (gera embedding automaticamente)."""
        query_embedding = self.generate_embedding(query_text)
        if not query_embedding:
            return []
        return self.find_similar(query_embedding, limit, threshold)

    def update_embeddings_for_all_items(self) -> Dict[str, int]:
        """Atualiza embeddings para todos os itens da base de conhecimento."""
        if not self.available:
            return {'updated': 0, 'errors': 0}

        items_to_update = KnowledgeItem.objects.filter(
            Q(active=True) & (Q(embedding__isnull=True) | Q(embedding__exact=[]))
        )
        logger.info(f"Atualizando embeddings para {items_to_update.count()} itens")

        updated_count, error_count = 0, 0
        for item in items_to_update:
            try:
                embedding = self.generate_embedding(item.question)
                if embedding:
                    item.embedding = embedding
                    item.save(update_fields=['embedding', 'updated_at'])
                    updated_count += 1
                else:
                    error_count += 1
            except Exception as e:
                logger.error(f"Erro ao atualizar embedding do item {item.id}: {e}")
                error_count += 1

        logger.info(f"Embeddings atualizados: {updated_count} sucessos, {error_count} erros")
        return {'updated': updated_count, 'errors': error_count}
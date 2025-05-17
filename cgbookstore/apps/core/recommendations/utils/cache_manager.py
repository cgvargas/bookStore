from django.core.cache import caches
from django.conf import settings
from typing import Optional, Dict, List
from django.contrib.auth import get_user_model

User = get_user_model()


class RecommendationCache:
    """Gerenciador de cache para recomendações usando caches específicos"""

    # Obter o cache específico para recomendações
    cache = caches['recommendations']
    books_cache = caches['books_recommendations']

    # Keys padrão para cache
    GENERAL_KEY = 'user_recommendations_{user_id}'
    SHELF_KEY = 'user_shelf_{user_id}'

    @classmethod
    def sanitize_cache_key(cls, key: str) -> str:
        """
        Sanitiza uma chave de cache
        Remove ou substitui caracteres problemáticos

        Args:
            key: Chave original do cache

        Returns:
            Chave sanitizada
        """
        # Remove espaços e caracteres especiais
        sanitized = key.replace(' ', '_')
        sanitized = ''.join(c for c in sanitized if c.isalnum() or c in ['_', '-'])

        # Garante comprimento máximo
        if len(sanitized) > 250:
            sanitized = sanitized[:250]

        return sanitized

    @classmethod
    def _get_general_key(cls, user_id: int) -> str:
        key = cls.GENERAL_KEY.format(user_id=user_id)
        return cls.sanitize_cache_key(key)

    @classmethod
    def _get_shelf_key(cls, user_id: int) -> str:
        key = cls.SHELF_KEY.format(user_id=user_id)
        return cls.sanitize_cache_key(key)

    @classmethod
    def get_recommendations(cls, user: User) -> Optional[List]:
        """Obtém recomendações do cache"""
        return cls.cache.get(cls._get_general_key(user.id))

    @classmethod
    def set_recommendations(cls, user: User, recommendations: List) -> None:
        """Armazena recomendações no cache"""
        cls.cache.set(
            cls._get_general_key(user.id),
            recommendations
            # Timeout gerenciado pela configuração do cache
        )

    @classmethod
    def get_shelf(cls, user: User) -> Optional[Dict]:
        """Obtém prateleira personalizada do cache"""
        return cls.books_cache.get(cls._get_shelf_key(user.id))

    @classmethod
    def set_shelf(cls, user: User, shelf_data: Dict) -> None:
        """Armazena prateleira personalizada no cache"""
        cls.books_cache.set(
            cls._get_shelf_key(user.id),
            shelf_data
            # Timeout gerenciado pela configuração do cache
        )

    @classmethod
    def invalidate_user_cache(cls, user: User) -> None:
        """Invalida todo o cache de um usuário"""
        cls.cache.delete(cls._get_general_key(user.id))
        cls.books_cache.delete(cls._get_shelf_key(user.id))

    @classmethod
    def get_recommendation_key(cls, user_id: int, shelf_hash: int, shelf_count: int, timestamp: int) -> str:
        """
        Gera uma chave de cache sanitizada para recomendações

        Args:
            user_id: ID do usuário
            shelf_hash: Hash da prateleira
            shelf_count: Quantidade de livros na prateleira
            timestamp: Timestamp atual

        Returns:
            Chave de cache sanitizada
        """
        base_key = f"recommendations_v8_{user_id}_{shelf_hash}_{shelf_count}_{timestamp}"
        return cls.sanitize_cache_key(base_key)
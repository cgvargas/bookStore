from django.core.cache import cache
from django.conf import settings
from typing import Optional, Dict, List
from django.contrib.auth import get_user_model

User = get_user_model()


class RecommendationCache:
    """Gerenciador de cache para recomendações"""

    # Keys padrão para cache
    GENERAL_KEY = 'user_recommendations_{user_id}'
    SHELF_KEY = 'user_shelf_{user_id}'

    # Tempo padrão de cache (24 horas)
    DEFAULT_TIMEOUT = 60 * 60 * 24

    @classmethod
    def sanitize_cache_key(cls, key: str) -> str:
        """
        Sanitiza uma chave de cache para uso com memcached
        Remove ou substitui caracteres problemáticos

        Args:
            key: Chave original do cache

        Returns:
            Chave sanitizada segura para uso com memcached
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
        return cache.get(cls._get_general_key(user.id))

    @classmethod
    def set_recommendations(cls, user: User, recommendations: List) -> None:
        """Armazena recomendações no cache"""
        cache.set(
            cls._get_general_key(user.id),
            recommendations,
            cls.DEFAULT_TIMEOUT
        )

    @classmethod
    def get_shelf(cls, user: User) -> Optional[Dict]:
        """Obtém prateleira personalizada do cache"""
        return cache.get(cls._get_shelf_key(user.id))

    @classmethod
    def set_shelf(cls, user: User, shelf_data: Dict) -> None:
        """Armazena prateleira personalizada no cache"""
        cache.set(
            cls._get_shelf_key(user.id),
            shelf_data,
            cls.DEFAULT_TIMEOUT
        )

    @classmethod
    def invalidate_user_cache(cls, user: User) -> None:
        """Invalida todo o cache de um usuário"""
        cache.delete(cls._get_general_key(user.id))
        cache.delete(cls._get_shelf_key(user.id))

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
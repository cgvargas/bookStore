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
    def _get_general_key(cls, user_id: int) -> str:
        return cls.GENERAL_KEY.format(user_id=user_id)

    @classmethod
    def _get_shelf_key(cls, user_id: int) -> str:
        return cls.SHELF_KEY.format(user_id=user_id)

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
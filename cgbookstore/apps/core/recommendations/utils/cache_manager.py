# Arquivo: cgbookstore/apps/core/recommendations/utils/cache_manager.py

from django.core.cache import caches, InvalidCacheBackendError
from django.utils import timezone
from typing import Optional, Dict, List, Any
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
import hashlib
import json
import logging
import re

logger = logging.getLogger(__name__)

class RecommendationCache:
    GENERAL_KEY = 'user_recommendations_v2_{user_id}'
    SHELF_KEY = 'user_shelf_v2_{user_id}'
    LANGUAGE_KEY = 'user_language_profile_v2_{user_id}'
    BEHAVIOR_KEY = 'user_behavior_v2_{user_id}'

    CACHE_TTL = {
        'recommendations': 3600,
        'shelf': 7200,
        'language_profile': 86400,
        'behavior': 43200,
    }

    INVALIDATION_EVENTS = {
        'book_added': ['recommendations', 'shelf'],
        'book_removed': ['recommendations', 'shelf', 'behavior'],
        'shelf_changed': ['recommendations', 'shelf', 'behavior'],
        'book_rated': ['recommendations', 'behavior'],
        'reading_completed': ['recommendations', 'language_profile', 'behavior'],
        'preference_updated': ['recommendations', 'language_profile', 'shelf', 'behavior'],
    }

    @classmethod
    def get_cache(cls):
        try:
            return caches['recommendations']
        except InvalidCacheBackendError:
            # Se o cache 'recommendations' não estiver configurado, usa o 'default'.
            logger.warning("Cache 'recommendations' não encontrado, usando 'default'.")
            return caches['default']

    @classmethod
    def get_books_cache(cls):
        try:
            # A forma correta de acessar um cache é com a sintaxe de dicionário.
            return caches['books_recommendations']
        except InvalidCacheBackendError:
            # Boa prática: se o cache 'books_recommendations' não estiver configurado,
            # usa o 'default' como alternativa.
            logger.warning("Cache 'books_recommendations' não encontrado, usando 'default'.")
            return caches['default']

    @classmethod
    def sanitize_cache_key(cls, key: str) -> str:
        key_with_underscores = re.sub(r'\s+', '_', key)
        sanitized = re.sub(r'[^a-zA-Z0-9_\-:.]', '', key_with_underscores)
        if len(sanitized) > 250:
            key_hash = hashlib.md5(sanitized.encode('utf-8')).hexdigest()
            sanitized = f"{sanitized[:200]}_{key_hash}"
        return sanitized

    @classmethod
    def _get_base_key_format(cls, key_template: str, user_id: int) -> str:
        return cls.sanitize_cache_key(key_template.format(user_id=user_id))

    @classmethod
    def _get_general_key(cls, user_id: int) -> str:
        return cls._get_base_key_format(cls.GENERAL_KEY, user_id)

    @classmethod
    def _get_shelf_key(cls, user_id: int) -> str:
        return cls._get_base_key_format(cls.SHELF_KEY, user_id)

    @classmethod
    def _get_language_key(cls, user_id: int) -> str:
        return cls._get_base_key_format(cls.LANGUAGE_KEY, user_id)

    @classmethod
    def _get_behavior_key(cls, user_id: int) -> str:
        return cls._get_base_key_format(cls.BEHAVIOR_KEY, user_id)

    @classmethod
    def get_recommendations(cls, user) -> Optional[Dict[str, Any]]:
        try:
            cache_data = cls.get_cache().get(cls._get_general_key(user.id))
            if cache_data and cls._is_cache_valid(cache_data, user):
                return cache_data
            return None
        except Exception as e:
            logger.error(f"Erro ao obter recomendações do cache para {user.id}: {e}", exc_info=True)
            return None

    @classmethod
    def set_recommendations(cls, user, recommendations: List[Any], metadata: Optional[Dict] = None) -> None:
        try:
            cache_data = {
                'recommendations': cls._serialize_recommendations(recommendations),
                'timestamp': timezone.now().isoformat(),
                'user_context': cls._get_user_context(user),
                'metadata': metadata or {},
                'version': '2.0'
            }
            cls.get_cache().set(
                cls._get_general_key(user.id),
                cache_data,
                cls.CACHE_TTL['recommendations']
            )
        except Exception as e:
            logger.error(f"Erro ao salvar recomendações no cache para {user.id}: {e}", exc_info=True)

    @classmethod
    def get_language_profile(cls, user) -> Optional[Dict]:
        try:
            return cls.get_cache().get(cls._get_language_key(user.id))
        except Exception as e:
            logger.error(f"Erro ao obter perfil de idioma do cache para {user.id}: {e}", exc_info=True)
            return None

    @classmethod
    def set_language_profile(cls, user, profile: Dict) -> None:
        try:
            cls.get_cache().set(
                cls._get_language_key(user.id),
                profile,
                cls.CACHE_TTL['language_profile']
            )
        except Exception as e:
            logger.error(f"Erro ao salvar perfil de idioma no cache para {user.id}: {e}", exc_info=True)

    @classmethod
    def get_user_behavior(cls, user) -> Optional[Dict]:
        try:
            return cls.get_cache().get(cls._get_behavior_key(user.id))
        except Exception as e:
            logger.error(f"Erro ao obter comportamento do usuário do cache para {user.id}: {e}", exc_info=True)
            return None

    @classmethod
    def set_user_behavior(cls, user, behavior: Dict) -> None:
        try:
            cls.get_cache().set(
                cls._get_behavior_key(user.id),
                behavior,
                cls.CACHE_TTL['behavior']
            )
        except Exception as e:
            logger.error(f"Erro ao salvar comportamento do usuário no cache para {user.id}: {e}", exc_info=True)

    @classmethod
    def get_shelf(cls, user) -> Optional[Dict]:
        try:
            return cls.get_books_cache().get(cls._get_shelf_key(user.id))
        except Exception as e:
            logger.error(f"Erro ao obter prateleira do cache para {user.id}: {e}", exc_info=True)
            return None

    @classmethod
    def set_shelf(cls, user, shelf_data: Dict) -> None:
        try:
            cls.get_books_cache().set(
                cls._get_shelf_key(user.id),
                shelf_data,
                cls.CACHE_TTL['shelf']
            )
        except Exception as e:
            logger.error(f"Erro ao salvar prateleira no cache para {user.id}: {e}", exc_info=True)

    @classmethod
    def invalidate_user_cache(cls, user, event: str = 'full') -> None:
        try:
            caches_to_invalidate_keys = []
            user_id = user if isinstance(user, int) else user.id
            if event == 'full':
                caches_to_invalidate_keys = [
                    cls._get_general_key(user_id),
                    cls._get_language_key(user_id),
                    cls._get_behavior_key(user_id),
                    cls._get_shelf_key(user_id)
                ]
            else:
                affected_cache_types = cls.INVALIDATION_EVENTS.get(event, [])
                for cache_type in affected_cache_types:
                    if cache_type == 'recommendations':
                        caches_to_invalidate_keys.append(cls._get_general_key(user_id))
                    elif cache_type == 'shelf':
                        caches_to_invalidate_keys.append(cls._get_shelf_key(user_id))
                    elif cache_type == 'language_profile':
                        caches_to_invalidate_keys.append(cls._get_language_key(user_id))
                    elif cache_type == 'behavior':
                        caches_to_invalidate_keys.append(cls._get_behavior_key(user_id))

            for key in caches_to_invalidate_keys:
                if cls.SHELF_KEY.format(user_id=user_id) in key:
                    cls.get_books_cache().delete(key)
                else:
                    cls.get_cache().delete(key)
        except Exception as e:
            logger.error(f"Erro ao invalidar cache para ID de usuário {user if isinstance(user, int) else user.id}, evento {event}: {e}", exc_info=True)

    @classmethod
    def _is_cache_valid(cls, cache_data: Dict, user) -> bool:
        try:
            if not isinstance(cache_data, dict) or cache_data.get('version') != '2.0':
                return False
            timestamp_str = cache_data.get('timestamp')
            if not timestamp_str:
                return False
            cache_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            if not cache_time.tzinfo:
                cache_time = timezone.make_aware(cache_time, timezone.utc)
            if timezone.now() - cache_time > timedelta(seconds=cls.CACHE_TTL['recommendations']):
                return False
            current_context = cls._get_user_context(user)
            cached_context = cache_data.get('user_context', {})
            if abs(current_context.get('total_books', 0) - cached_context.get('total_books', 0)) > 1:
                return False
            if current_context.get('favorite_category') != cached_context.get('favorite_category'):
                return False
            return True
        except Exception as e:
            logger.error(f"Erro ao validar cache para {user.id}: {e}", exc_info=True)
            return False

    @classmethod
    def _get_user_context(cls, user) -> Dict:
        try:
            from ...models import UserBookShelf
            user_books = UserBookShelf.objects.filter(user=user).select_related('book')
            shelf_counts: Dict[str, int] = {}
            categories: Dict[str, int] = {}
            for shelf in user_books:
                shelf_type = shelf.shelf_type
                shelf_counts[shelf_type] = shelf_counts.get(shelf_type, 0) + 1
                if shelf.book and shelf.book.categoria:
                    cat_name = shelf.book.categoria
                    categories[str(cat_name)] = categories.get(str(cat_name), 0) + 1
            favorite_category = max(categories.items(), key=lambda x: x[1])[0] if categories else None
            last_activity_obj = user_books.order_by('-added_at').first()
            last_activity_ts = last_activity_obj.added_at.isoformat() if last_activity_obj else None
            return {
                'total_books': user_books.count(),
                'shelf_counts': shelf_counts,
                'favorite_category': favorite_category,
                'last_activity': last_activity_ts
            }
        except Exception as e:
            logger.error(f"Erro ao obter contexto do usuário para {user.id}: {e}", exc_info=True)
            return {}

    @classmethod
    def _serialize_recommendations(cls, recommendations: List[Any]) -> List[Dict]:
        serialized = []
        for item in recommendations:
            try:
                if isinstance(item, dict):
                    serialized.append({'type': 'external', 'data': item})
                elif hasattr(item, 'id') and hasattr(item, 'titulo'):
                    serialized.append({
                        'type': 'local',
                        'id': item.id,
                        'titulo': item.titulo,
                        'autor': getattr(item, 'autor', None),
                        'categoria': getattr(item, 'categoria', None),
                        'idioma': getattr(item, 'idioma', None)
                    })
            except Exception as e:
                logger.warning(f"Erro ao serializar recomendação: {e}", exc_info=True)
        return serialized

    @classmethod
    def warm_cache(cls, user) -> None:
        try:
            from ..providers.language_preference import LanguagePreferenceProvider
            from ..engine import RecommendationEngine
            language_provider = LanguagePreferenceProvider()
            language_profile = language_provider.get_language_affinity(user)
            if language_profile:
                cls.set_language_profile(user, language_profile)
            engine = RecommendationEngine()
            behavior = engine._analyze_user_behavior(user)
            if behavior:
                cls.set_user_behavior(user, behavior)
        except Exception as e:
            logger.error(f"Erro ao aquecer cache para {user.id}: {e}", exc_info=True)

    @classmethod
    def get_cache_stats(cls, user) -> Dict:
        stats = {'recommendations': False, 'shelf': False, 'language_profile': False, 'behavior': False}
        try:
            if cls.get_cache().get(cls._get_general_key(user.id)):
                stats['recommendations'] = True
            if cls.get_books_cache().get(cls._get_shelf_key(user.id)):
                stats['shelf'] = True
            if cls.get_cache().get(cls._get_language_key(user.id)):
                stats['language_profile'] = True
            if cls.get_cache().get(cls._get_behavior_key(user.id)):
                stats['behavior'] = True
            return stats
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas de cache para {user.id}: {e}", exc_info=True)
            return stats
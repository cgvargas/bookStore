# cgbookstore/apps/core/recommendations/utils/cache_manager.py

from django.core.cache import caches
from django.conf import settings
from django.utils import timezone
from typing import Optional, Dict, List, Any, Set
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
import hashlib
import json
import logging
import unicodedata
import re

User = get_user_model()
logger = logging.getLogger(__name__)


class RecommendationCache:
    """
    Gerenciador de cache inteligente para recomendações
    com invalidação baseada em eventos e análise de mudanças
    """

    GENERAL_KEY = 'user_recommendations_v2_{user_id}' # Adicionada versão na chave para evitar conflitos com formatos antigos
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
        'book_added': ['recommendations', 'shelf'],  # Removido 'behavior' - comportamento é mais estável
        'book_removed': ['recommendations', 'shelf', 'behavior'],
        # Manter behavior aqui pois remover pode afetar padrões
        'shelf_changed': ['recommendations', 'shelf', 'behavior'],
        # Mudança de tipo de prateleira pode afetar comportamento
        'book_rated': ['recommendations', 'behavior'],  # Avaliação afeta recomendações e comportamento
        'reading_completed': ['recommendations', 'language_profile', 'behavior'],
        # Completar leitura pode mudar padrões
        'preference_updated': ['recommendations', 'language_profile', 'shelf', 'behavior'],
        # Mudança de preferência afeta tudo
    }

    @classmethod
    def get_cache(cls):
        return caches['recommendations']

    @classmethod
    def get_books_cache(cls):
        # Usa try/except para acessar cache configurado ou fallback para default
        try:
            return caches['books_recommendations']
        except KeyError:
            return caches['default']

    @classmethod
    def sanitize_cache_key(cls, key: str) -> str:
        """
        Sanitiza chave de cache removendo acentos e caracteres especiais
        """
        # Primeiro substitui espaços por underscores
        key_with_underscores = re.sub(r'\s+', '_', key)

        # Remove caracteres especiais E acentuados, mantém apenas letras ASCII, números, hífen, underscore e alguns símbolos seguros
        sanitized = re.sub(r'[^a-zA-Z0-9_\-:.]', '', key_with_underscores)

        # Garante que não seja muito longo (limite do memcached é 250 caracteres)
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
    def get_recommendations(cls, user: User) -> Optional[Dict[str, Any]]:
        try:
            cache_data = cls.get_cache().get(cls._get_general_key(user.id))
            if cache_data and cls._is_cache_valid(cache_data, user):
                logger.debug(f"Cache hit para recomendações do usuário {user.id}")
                return cache_data
            logger.debug(f"Cache miss para recomendações do usuário {user.id}")
            return None
        except Exception as e:
            logger.error(f"Erro ao obter recomendações do cache para {user.id}: {e}", exc_info=True)
            return None

    @classmethod
    def set_recommendations(cls, user: User, recommendations: List[Any], metadata: Optional[Dict] = None) -> None:
        try:
            cache_data = {
                'recommendations': cls._serialize_recommendations(recommendations),
                'timestamp': timezone.now().isoformat(),
                'user_context': cls._get_user_context(user),
                'metadata': metadata or {},
                'version': '2.0'  # Versão da estrutura do cache
            }
            cls.get_cache().set(
                cls._get_general_key(user.id),
                cache_data,
                cls.CACHE_TTL['recommendations']
            )
            logger.debug(f"Cache de recomendações atualizado para usuário {user.id}")
        except Exception as e:
            logger.error(f"Erro ao salvar recomendações no cache para {user.id}: {e}", exc_info=True)

    @classmethod
    def get_language_profile(cls, user: User) -> Optional[Dict]:
        try:
            return cls.get_cache().get(cls._get_language_key(user.id))
        except Exception as e:
            logger.error(f"Erro ao obter perfil de idioma do cache para {user.id}: {e}", exc_info=True)
            return None

    @classmethod
    def set_language_profile(cls, user: User, profile: Dict) -> None:
        try:
            cls.get_cache().set(
                cls._get_language_key(user.id),
                profile,
                cls.CACHE_TTL['language_profile']
            )
        except Exception as e:
            logger.error(f"Erro ao salvar perfil de idioma no cache para {user.id}: {e}", exc_info=True)


    @classmethod
    def get_user_behavior(cls, user: User) -> Optional[Dict]:
        try:
            return cls.get_cache().get(cls._get_behavior_key(user.id))
        except Exception as e:
            logger.error(f"Erro ao obter comportamento do usuário do cache para {user.id}: {e}", exc_info=True)
            return None

    @classmethod
    def set_user_behavior(cls, user: User, behavior: Dict) -> None:
        try:
            cls.get_cache().set(
                cls._get_behavior_key(user.id),
                behavior,
                cls.CACHE_TTL['behavior']
            )
        except Exception as e:
            logger.error(f"Erro ao salvar comportamento do usuário no cache para {user.id}: {e}", exc_info=True)

    @classmethod
    def get_shelf(cls, user: User) -> Optional[Dict]:
        try:
            return cls.get_books_cache().get(cls._get_shelf_key(user.id))
        except Exception as e:
            logger.error(f"Erro ao obter prateleira do cache para {user.id}: {e}", exc_info=True)
            return None

    @classmethod
    def set_shelf(cls, user: User, shelf_data: Dict) -> None:
        try:
            cls.get_books_cache().set(
                cls._get_shelf_key(user.id),
                shelf_data,
                cls.CACHE_TTL['shelf']
            )
        except Exception as e:
            logger.error(f"Erro ao salvar prateleira no cache para {user.id}: {e}", exc_info=True)


    @classmethod
    def invalidate_user_cache(cls, user: User, event: str = 'full') -> None:
        try:
            caches_to_invalidate_keys = []
            if event == 'full':
                caches_to_invalidate_keys = [
                    cls._get_general_key(user.id),
                    cls._get_language_key(user.id),
                    cls._get_behavior_key(user.id),
                    cls._get_shelf_key(user.id) # Chave para books_cache
                ]
                logger.info(f"Cache totalmente invalidado para usuário {user.id}")
            else:
                affected_cache_types = cls.INVALIDATION_EVENTS.get(event, [])
                for cache_type in affected_cache_types:
                    if cache_type == 'recommendations':
                        caches_to_invalidate_keys.append(cls._get_general_key(user.id))
                    elif cache_type == 'shelf':
                        caches_to_invalidate_keys.append(cls._get_shelf_key(user.id))
                    elif cache_type == 'language_profile':
                        caches_to_invalidate_keys.append(cls._get_language_key(user.id))
                    elif cache_type == 'behavior':
                        caches_to_invalidate_keys.append(cls._get_behavior_key(user.id))
                logger.info(f"Cache invalidado seletivamente para evento '{event}' do usuário {user.id} (tipos: {affected_cache_types})")

            for key in caches_to_invalidate_keys:
                if cls.SHELF_KEY.format(user_id=user.id) in key: # Identifica se é chave do shelf_cache
                    cls.get_books_cache().delete(key)
                else:
                    cls.get_cache().delete(key)
        except Exception as e:
            logger.error(f"Erro ao invalidar cache para {user.id}, evento {event}: {e}", exc_info=True)


    @classmethod
    def _is_cache_valid(cls, cache_data: Dict, user: User) -> bool:
        try:
            if not isinstance(cache_data, dict): # Verificação básica de tipo
                return False

            if cache_data.get('version') != '2.0':
                logger.debug(f"Cache inválido para {user.id}: versão incorreta.")
                return False

            timestamp_str = cache_data.get('timestamp')
            if not timestamp_str:
                logger.debug(f"Cache inválido para {user.id}: timestamp ausente.")
                return False

            try:
                cache_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                if not cache_time.tzinfo: # Se for naive, torna aware com UTC
                     cache_time = timezone.make_aware(cache_time, timezone.utc)
            except ValueError:
                logger.warning(f"Cache inválido para {user.id}: formato de timestamp inválido '{timestamp_str}'.")
                return False

            # Usar timezone.now() que é aware por padrão
            if timezone.now() - cache_time > timedelta(seconds=cls.CACHE_TTL['recommendations']):
                logger.debug(f"Cache inválido para {user.id}: expirado (TTL: {cls.CACHE_TTL['recommendations']}s).")
                return False

            current_context = cls._get_user_context(user)
            cached_context = cache_data.get('user_context', {})

            # Alterado para > 1 (diferença de 2 livros ou mais invalida)
            if abs(current_context.get('total_books', 0) - cached_context.get('total_books', 0)) > 1:
                logger.debug(f"Cache inválido para {user.id}: mudança significativa no total de livros.")
                return False

            if current_context.get('favorite_category') != cached_context.get('favorite_category'):
                logger.debug(f"Cache inválido para {user.id}: mudança na categoria favorita.")
                return False

            return True
        except Exception as e:
            logger.error(f"Erro ao validar cache para {user.id}: {e}", exc_info=True)
            return False

    @classmethod
    def _get_user_context(cls, user: User) -> Dict:
        try:
            from ...models import UserBookShelf  # Ajuste na importação relativa se necessário
            # (assumindo que UserBookShelf está em core.models)

            # Removido select_related com campos inexistentes
            user_books = UserBookShelf.objects.filter(user=user).select_related('book')

            shelf_counts: Dict[str, int] = {}
            categories: Dict[str, int] = {}

            for shelf in user_books:
                shelf_type = shelf.shelf_type
                shelf_counts[shelf_type] = shelf_counts.get(shelf_type, 0) + 1

                if shelf.book and shelf.book.categoria:  # Usar categoria do livro
                    cat_name = shelf.book.categoria  # Assumindo que categoria é um campo simples ou ForeignKey com __str__
                    if hasattr(cat_name, 'name'):  # Se for um objeto Categoria
                        cat_name = cat_name.name
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
                if isinstance(item, dict): # Recomendação externa
                    serialized.append({
                        'type': 'external',
                        'data': item
                    })
                elif hasattr(item, 'id') and hasattr(item, 'titulo'): # Assumindo ser um objeto Book-like
                    serialized.append({
                        'type': 'local',
                        'id': item.id,
                        'titulo': item.titulo,
                        'autor': getattr(item, 'autor', None), # Usar getattr para segurança
                        'categoria': getattr(item, 'categoria', None),
                        'idioma': getattr(item, 'idioma', None)
                    })
                else:
                    logger.warning(f"Item de recomendação não serializável encontrado: {type(item)}")
            except Exception as e:
                logger.warning(f"Erro ao serializar recomendação: {e}", exc_info=True)
        return serialized

    @classmethod
    def get_recommendation_key(cls, user_id: int, context_hash: str) -> str:
        base_key = f"rec_v2_{user_id}_{context_hash}"
        return cls.sanitize_cache_key(base_key)

    @classmethod
    def warm_cache(cls, user: User) -> None:
        try:
            from ..providers.language_preference import LanguagePreferenceProvider
            from ..engine import RecommendationEngine

            logger.info(f"Aquecendo cache para usuário {user.id}")

            language_provider = LanguagePreferenceProvider()
            language_profile = language_provider.get_language_affinity(user)
            if language_profile: # Verifica se o perfil não é None
                cls.set_language_profile(user, language_profile)

            engine = RecommendationEngine() # Instancia o engine
            behavior = engine._analyze_user_behavior(user) # Chama o método na instância
            if behavior: # Verifica se o comportamento não é None
                cls.set_user_behavior(user, behavior)

            logger.info(f"Cache aquecido para usuário {user.id}")
        except Exception as e:
            logger.error(f"Erro ao aquecer cache para {user.id}: {e}", exc_info=True)

    @classmethod
    def get_cache_stats(cls, user: User) -> Dict:
        stats = {
            'recommendations': False,
            'shelf': False,
            'language_profile': False,
            'behavior': False,
        }
        try:
            if cls.get_cache().get(cls._get_general_key(user.id)) is not None: # <--- CORREÇÃO APLICADA
                stats['recommendations'] = True
            if cls.get_books_cache().get(cls._get_shelf_key(user.id)) is not None: # <--- CORREÇÃO APLICADA
                stats['shelf'] = True
            if cls.get_cache().get(cls._get_language_key(user.id)) is not None: # <--- CORREÇÃO APLICADA
                stats['language_profile'] = True
            if cls.get_cache().get(cls._get_behavior_key(user.id)) is not None: # <--- CORREÇÃO APLICADA
                stats['behavior'] = True
            return stats
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas de cache para {user.id}: {e}", exc_info=True)
            return stats
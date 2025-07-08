import json
import logging
from typing import Optional, List, Dict, Any, Union
from datetime import timedelta
from django.core.cache import caches, cache
from django.conf import settings
import redis

logger = logging.getLogger(__name__)


class RedisHelper:
    """
    Utilitário para gerenciar operações Redis no projeto Django
    """

    def __init__(self, cache_name: str = 'default'):
        """
        Inicializa o helper Redis

        Args:
            cache_name: Nome do cache configurado no Django (default: 'default')
        """
        self.cache_name = cache_name
        self.cache = caches[cache_name]

        try:
            self.client = self.cache.client.get_client(write=True)
        except Exception as e:
            logger.error(f"Erro ao conectar com Redis: {e}")
            self.client = None

    def is_connected(self) -> bool:
        """
        Verifica se a conexão com Redis está ativa

        Returns:
            bool: True se conectado, False caso contrário
        """
        try:
            return self.client.ping() if self.client else False
        except Exception:
            return False

    # =============================================
    # OPERAÇÕES BÁSICAS DE CACHE
    # =============================================

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """
        Define um valor no cache

        Args:
            key: Chave do cache
            value: Valor a ser armazenado
            timeout: Tempo de expiração em segundos (None = sem expiração)

        Returns:
            bool: True se sucesso, False caso contrário
        """
        try:
            self.cache.set(key, value, timeout)
            return True
        except Exception as e:
            logger.error(f"Erro ao definir cache {key}: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtém um valor do cache

        Args:
            key: Chave do cache
            default: Valor padrão se chave não existir

        Returns:
            Valor do cache ou default
        """
        try:
            return self.cache.get(key, default)
        except Exception as e:
            logger.error(f"Erro ao obter cache {key}: {e}")
            return default

    def delete(self, key: str) -> bool:
        """
        Remove uma chave do cache

        Args:
            key: Chave a ser removida

        Returns:
            bool: True se sucesso, False caso contrário
        """
        try:
            self.cache.delete(key)
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar cache {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """
        Verifica se uma chave existe no cache

        Args:
            key: Chave a verificar

        Returns:
            bool: True se existe, False caso contrário
        """
        try:
            return self.cache.get(key) is not None
        except Exception as e:
            logger.error(f"Erro ao verificar existência de {key}: {e}")
            return False

    # =============================================
    # OPERAÇÕES ESPECÍFICAS PARA LIVROS
    # =============================================

    def cache_book_data(self, book_id: Union[int, str], data: Dict, timeout: int = 3600) -> bool:
        """
        Armazena dados de um livro no cache

        Args:
            book_id: ID do livro
            data: Dados do livro
            timeout: Tempo de expiração (default: 1 hora)

        Returns:
            bool: True se sucesso
        """
        key = f"book_data_{book_id}"
        return self.set(key, data, timeout)

    def get_book_data(self, book_id: Union[int, str]) -> Optional[Dict]:
        """
        Obtém dados de um livro do cache

        Args:
            book_id: ID do livro

        Returns:
            Dict com dados do livro ou None
        """
        key = f"book_data_{book_id}"
        return self.get(key)

    def cache_recommendations(self, user_id: Optional[int], recommendations: List[Dict],
                              timeout: int = 1800) -> bool:
        """
        Armazena recomendações no cache

        Args:
            user_id: ID do usuário (None para recomendações gerais)
            recommendations: Lista de recomendações
            timeout: Tempo de expiração (default: 30 minutos)

        Returns:
            bool: True se sucesso
        """
        key = f"recommendations_{user_id or 'general'}"
        return self.set(key, recommendations, timeout)

    def get_recommendations(self, user_id: Optional[int]) -> Optional[List[Dict]]:
        """
        Obtém recomendações do cache

        Args:
            user_id: ID do usuário (None para recomendações gerais)

        Returns:
            Lista de recomendações ou None
        """
        key = f"recommendations_{user_id or 'general'}"
        return self.get(key)

    def cache_google_books_data(self, external_id: str, data: Dict, timeout: int = 86400) -> bool:
        """
        Armazena dados da API Google Books no cache

        Args:
            external_id: ID externo do livro (Google Books)
            data: Dados da API
            timeout: Tempo de expiração (default: 24 horas)

        Returns:
            bool: True se sucesso
        """
        key = f"google_books_{external_id}"
        return self.set(key, data, timeout)

    def get_google_books_data(self, external_id: str) -> Optional[Dict]:
        """
        Obtém dados da API Google Books do cache

        Args:
            external_id: ID externo do livro

        Returns:
            Dict com dados da API ou None
        """
        key = f"google_books_{external_id}"
        return self.get(key)

    # =============================================
    # OPERAÇÕES DE LIMPEZA SELETIVA
    # =============================================

    def clear_book_cache(self, book_id: Union[int, str]) -> bool:
        """
        Limpa cache específico de um livro

        Args:
            book_id: ID do livro

        Returns:
            bool: True se sucesso
        """
        patterns = [
            f"book_data_{book_id}",
            f"book_details_{book_id}",
            f"book_reviews_{book_id}",
        ]

        success = True
        for pattern in patterns:
            if not self.delete(pattern):
                success = False

        return success

    def clear_recommendations_cache(self, user_id: Optional[int] = None) -> bool:
        """
        Limpa cache de recomendações

        Args:
            user_id: ID do usuário específico (None = todas as recomendações)

        Returns:
            bool: True se sucesso
        """
        if user_id is not None:
            return self.delete(f"recommendations_{user_id}")

        # Limpar todas as recomendações se user_id for None
        try:
            if self.client:
                keys = self.client.keys("recommendations_*")
                if keys:
                    deleted = self.client.delete(*keys)
                    logger.info(f"Removidas {deleted} chaves de recomendações")
                return True
        except Exception as e:
            logger.error(f"Erro ao limpar cache de recomendações: {e}")
            return False

    def clear_google_books_cache(self, external_id: Optional[str] = None) -> bool:
        """
        Limpa cache da API Google Books

        Args:
            external_id: ID específico (None = todos os dados da API)

        Returns:
            bool: True se sucesso
        """
        if external_id is not None:
            return self.delete(f"google_books_{external_id}")

        # Limpar todos os dados da API se external_id for None
        try:
            if self.client:
                keys = self.client.keys("google_books_*")
                if keys:
                    deleted = self.client.delete(*keys)
                    logger.info(f"Removidas {deleted} chaves da API Google Books")
                return True
        except Exception as e:
            logger.error(f"Erro ao limpar cache da API Google Books: {e}")
            return False

    def clear_books_cache_safely(self) -> Dict[str, int]:
        """
        Limpa cache relacionado a livros preservando dados críticos

        Returns:
            Dict com estatísticas de limpeza
        """
        stats = {
            'books_cleared': 0,
            'recommendations_cleared': 0,
            'google_books_cleared': 0,
            'errors': 0
        }

        try:
            if not self.client:
                return stats

            # Padrões seguros para limpar
            safe_patterns = [
                'book_*',
                'recommendations_*',
                'google_books_*',
                'livro_*',
                'recomend*'
            ]

            # Padrões críticos para NÃO limpar
            critical_patterns = [
                'kombu',
                'celery',
                'session',
                'csrf',
                'django',
                'admin'
            ]

            total_cleared = 0

            for pattern in safe_patterns:
                try:
                    keys = self.client.keys(pattern)
                    # Filtrar chaves críticas
                    safe_keys = [
                        k for k in keys
                        if not any(critical in k.decode('utf-8', errors='ignore').lower()
                                   for critical in critical_patterns)
                    ]

                    if safe_keys:
                        deleted = self.client.delete(*safe_keys)
                        total_cleared += deleted

                        # Categorizar por tipo
                        for key in safe_keys:
                            key_str = key.decode('utf-8', errors='ignore').lower()
                            if 'book' in key_str or 'livro' in key_str:
                                stats['books_cleared'] += 1
                            elif 'recommend' in key_str:
                                stats['recommendations_cleared'] += 1
                            elif 'google' in key_str:
                                stats['google_books_cleared'] += 1

                except Exception as e:
                    logger.error(f"Erro ao limpar padrão {pattern}: {e}")
                    stats['errors'] += 1

            logger.info(f"Cache de livros limpo: {total_cleared} chaves removidas")

        except Exception as e:
            logger.error(f"Erro geral ao limpar cache de livros: {e}")
            stats['errors'] += 1

        return stats

    # =============================================
    # OPERAÇÕES DE MONITORAMENTO
    # =============================================

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas do cache

        Returns:
            Dict com estatísticas
        """
        stats = {
            'connected': self.is_connected(),
            'total_keys': 0,
            'book_keys': 0,
            'recommendation_keys': 0,
            'google_books_keys': 0,
            'memory_usage': 'N/A',
            'connection_info': {}
        }

        try:
            if not self.client:
                return stats

            # Total de chaves
            stats['total_keys'] = self.client.dbsize()

            # Contar chaves por categoria
            book_keys = self.client.keys('*book*') + self.client.keys('*livro*')
            stats['book_keys'] = len(book_keys)

            rec_keys = self.client.keys('*recommend*') + self.client.keys('*recomend*')
            stats['recommendation_keys'] = len(rec_keys)

            google_keys = self.client.keys('*google_books*')
            stats['google_books_keys'] = len(google_keys)

            # Informações do servidor
            info = self.client.info()
            stats['memory_usage'] = info.get('used_memory_human', 'N/A')

            # Informações de conexão
            conn_info = self.client.connection_pool.connection_kwargs
            stats['connection_info'] = {
                'host': conn_info.get('host', 'N/A'),
                'port': conn_info.get('port', 'N/A'),
                'db': conn_info.get('db', 'N/A')
            }

        except Exception as e:
            logger.error(f"Erro ao obter estatísticas do cache: {e}")

        return stats

    def get_key_info(self, key: str) -> Dict[str, Any]:
        """
        Obtém informações detalhadas sobre uma chave

        Args:
            key: Chave a analisar

        Returns:
            Dict com informações da chave
        """
        info = {
            'exists': False,
            'type': None,
            'ttl': None,
            'size': None,
            'value_preview': None
        }

        try:
            if not self.client:
                return info

            # Verificar existência
            info['exists'] = bool(self.client.exists(key))

            if info['exists']:
                # Tipo da chave
                info['type'] = self.client.type(key).decode('utf-8')

                # TTL
                ttl = self.client.ttl(key)
                if ttl >= 0:
                    info['ttl'] = ttl
                elif ttl == -1:
                    info['ttl'] = 'never_expires'
                else:
                    info['ttl'] = 'expired'

                # Obter valor via Django cache para preview
                try:
                    cache_key = key.replace('default:1:', '') if 'default:1:' in key else key
                    value = self.cache.get(cache_key)

                    if value is not None:
                        if isinstance(value, (dict, list)):
                            info['value_preview'] = f"{type(value).__name__} with {len(value)} items"
                        elif isinstance(value, str):
                            preview = value[:100] + '...' if len(value) > 100 else value
                            info['value_preview'] = f"String: {preview}"
                        else:
                            info['value_preview'] = f"{type(value).__name__}: {str(value)[:100]}"
                except Exception:
                    info['value_preview'] = "Unable to preview"

        except Exception as e:
            logger.error(f"Erro ao obter informações da chave {key}: {e}")

        return info


# =============================================
# INSTÂNCIA GLOBAL PARA FACILITAR USO
# =============================================

# Instância padrão do helper
redis_helper = RedisHelper()


# =============================================
# DECORATORS ÚTEIS
# =============================================

def cache_result(key_prefix: str, timeout: int = 3600):
    """
    Decorator para cachear resultado de funções

    Args:
        key_prefix: Prefixo da chave do cache
        timeout: Tempo de expiração em segundos
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Criar chave única baseada nos argumentos
            key_parts = [key_prefix, func.__name__]
            key_parts.extend([str(arg) for arg in args])
            key_parts.extend([f"{k}_{v}" for k, v in sorted(kwargs.items())])

            cache_key = "_".join(key_parts)

            # Tentar obter do cache
            result = redis_helper.get(cache_key)

            if result is not None:
                logger.debug(f"Cache hit para {cache_key}")
                return result

            # Executar função e cachear resultado
            result = func(*args, **kwargs)
            redis_helper.set(cache_key, result, timeout)
            logger.debug(f"Cache miss para {cache_key} - resultado cacheado")

            return result

        return wrapper

    return decorator


def invalidate_cache_on_save(key_patterns: List[str]):
    """
    Decorator para invalidar cache quando modelo for salvo

    Args:
        key_patterns: Lista de padrões de chave para invalidar
    """

    def decorator(func):
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)

            # Invalidar cache após save
            try:
                if redis_helper.client:
                    for pattern in key_patterns:
                        # Substituir placeholders com valores do objeto
                        if hasattr(self, 'id'):
                            pattern = pattern.replace('{id}', str(self.id))
                        if hasattr(self, 'external_id'):
                            pattern = pattern.replace('{external_id}', str(self.external_id or ''))

                        keys = redis_helper.client.keys(pattern)
                        if keys:
                            redis_helper.client.delete(*keys)
                            logger.info(f"Cache invalidado: {len(keys)} chaves removidas para padrão {pattern}")

            except Exception as e:
                logger.error(f"Erro ao invalidar cache: {e}")

            return result

        return wrapper

    return decorator
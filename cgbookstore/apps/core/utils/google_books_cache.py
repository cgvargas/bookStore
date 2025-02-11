"""
Módulo de cache para API do Google Books.

Fornece mecanismo de cache para consultas à API do Google Books,
melhorando performance e reduzindo chamadas repetidas.

Características:
- Geração de chaves de cache únicas
- Tratamento de erros de cache
- Decorador para cachear resultados de métodos
"""

from functools import wraps
from django.core.cache import caches
from django.conf import settings
import hashlib
import json
import logging

# Configuração de logger para rastreamento de eventos de cache
logger = logging.getLogger(__name__)


class GoogleBooksCache:
    """
    Gerenciador de cache para consultas do Google Books.

    Responsabilidades:
    - Inicializar cache com configurações personalizadas
    - Gerar chaves de cache únicas
    - Recuperar e definir dados em cache

    Características:
    - Utiliza backend de cache configurado
    - Gera chaves baseadas em hash MD5
    - Configura tempo de expiração do cache
    """

    def __init__(self):
        """
        Inicializa o gerenciador de cache.

        Configura:
        - Backend de cache
        - Tempo de expiração
        - Prefixo de chave de cache
        """
        self.cache = caches['google_books']
        self.timeout = settings.GOOGLE_BOOKS_CACHE_TIMEOUT
        self.prefix = settings.GOOGLE_BOOKS_CACHE_KEY_PREFIX

    def generate_key(self, *args, **kwargs):
        """
        Gera uma chave de cache única baseada nos argumentos.

        Características:
        - Converte argumentos para JSON
        - Gera hash MD5 para garantir unicidade

        Args:
            *args: Argumentos posicionais
            **kwargs: Argumentos nomeados

        Returns:
            str: Chave de cache única
        """
        key_data = json.dumps({'args': args, 'kwargs': kwargs}, sort_keys=True)
        return f"{self.prefix}{hashlib.md5(key_data.encode()).hexdigest()}"

    def get(self, key):
        """
        Recupera valor do cache.

        Args:
            key (str): Chave de cache

        Returns:
            Valor em cache ou None em caso de erro
        """
        try:
            return self.cache.get(key)
        except Exception as e:
            logger.error(f"Erro ao recuperar cache: {str(e)}")
            return None

    def set(self, key, value):
        """
        Define valor no cache.

        Args:
            key (str): Chave de cache
            value: Valor a ser armazenado

        Returns:
            bool: True se sucesso, False em caso de erro
        """
        try:
            self.cache.set(key, value, self.timeout)
            return True
        except Exception as e:
            logger.error(f"Erro ao definir cache: {str(e)}")
            return False


# Instância global de cache
cache_instance = GoogleBooksCache()


def cache_google_books_api(func):
    """
    Decorador para cachear resultados de métodos da API do Google Books.

    Características:
    - Verifica cache antes de executar método
    - Armazena resultado em cache se não existir

    Args:
        func (callable): Método a ser decorado

    Returns:
        callable: Método decorado com lógica de cache
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        """
        Wrapper para adicionar funcionalidade de cache.

        Args:
            self: Instância do método
            *args: Argumentos posicionais
            **kwargs: Argumentos nomeados

        Returns:
            Resultado do método, recuperado do cache ou executado
        """
        # Gera chave de cache única baseada nos argumentos
        cache_key = cache_instance.generate_key(*args, **kwargs)

        # Tenta recuperar resultado do cache
        result = cache_instance.get(cache_key)

        # Se não estiver em cache, executa método e salva
        if result is None:
            result = func(self, *args, **kwargs)
            cache_instance.set(cache_key, result)

        return result

    return wrapper
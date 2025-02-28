"""
Serviço centralizado para comunicação com a API do Google Books.
Este módulo é compartilhado entre o sistema de busca e o sistema de recomendações.
"""
import requests
import json
import logging
import hashlib
from typing import List, Dict, Any, Optional
from django.conf import settings
from django.core.cache import caches
from functools import wraps
import time

logger = logging.getLogger(__name__)

# Configurações do cache
CACHE_KEY_PREFIX = "gb_api"
CACHE_TIMEOUT = 60 * 60 * 24  # 24 horas
SEARCH_CACHE_TIMEOUT = 60 * 60 * 2  # 2 horas para buscas


class GoogleBooksCache:
    """
    Implementação centralizada de cache para API do Google Books.
    Utilizada por ambos os sistemas de busca e recomendações.
    """

    def __init__(self, namespace="google_books", timeout=None):
        """Inicializa o cache com configurações personalizáveis"""
        self._cache = caches['default']
        self.NAMESPACE = namespace
        self.DEFAULT_TIMEOUT = timeout or CACHE_TIMEOUT

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Obtém dados do cache"""
        cache_key = self._get_full_key(key)
        data = self._cache.get(cache_key)

        if data:
            try:
                if isinstance(data, str):
                    return json.loads(data)
                return data
            except json.JSONDecodeError:
                logger.warning(f"Erro ao decodificar dados do cache para {key}")
                return None

        return None

    def set(self, key: str, data: Any, timeout: int = None) -> None:
        """Armazena dados no cache"""
        if timeout is None:
            timeout = self.DEFAULT_TIMEOUT

        cache_key = self._get_full_key(key)

        try:
            if isinstance(data, (dict, list)):
                data_str = json.dumps(data)
                self._cache.set(cache_key, data_str, timeout)
            else:
                self._cache.set(cache_key, data, timeout)
        except Exception as e:
            logger.error(f"Erro ao armazenar dados no cache: {str(e)}")

    def delete(self, key: str) -> None:
        """Remove dados do cache"""
        cache_key = self._get_full_key(key)
        self._cache.delete(cache_key)

    def _get_full_key(self, key: str) -> str:
        """Gera chave completa com namespace"""
        # Sanitizar a chave para evitar problemas com caracteres especiais
        safe_key = hashlib.md5(key.encode('utf-8')).hexdigest()
        return f"{self.NAMESPACE}:{safe_key}"

    def generate_key(self, *args, **kwargs) -> str:
        """Gera uma chave única baseada nos argumentos"""
        key_data = json.dumps({'args': args, 'kwargs': kwargs}, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()


class GoogleBooksClient:
    """
    Cliente centralizado para API do Google Books.
    Usado por ambos os sistemas de busca e recomendações.
    """

    def __init__(self, cache_namespace=None, context=None):
        """
        Inicializa o cliente

        Args:
            cache_namespace: Opcional - namespace para isolar o cache
            context: Opcional - contexto para identificar quem está usando (busca ou recomendações)
        """
        self.base_url = "https://www.googleapis.com/books/v1"
        self.api_key = getattr(settings, 'GOOGLE_BOOKS_API_KEY', None)

        # Permitir namespaces diferentes para isolamento de cache entre módulos
        self.cache = GoogleBooksCache(
            namespace=cache_namespace or "google_books",
            timeout=CACHE_TIMEOUT
        )

        self.default_timeout = 5  # timeout em segundos
        self.context = context or "general"
        logger.info(f"GoogleBooksClient inicializado para contexto: {self.context}")

    def search_books(self, query: str, max_results: int = 10, search_type: str = None,
                     page: int = 1, items_per_page: int = None) -> Dict[str, Any]:
        """
        Busca livros na API do Google Books
        """
        print(f"[{self.context}] Iniciando busca com: {query}, tipo: {search_type}, max_results: {max_results}")

        # Formatar a consulta baseada no tipo de busca
        formatted_query = query
        if search_type and search_type != 'all':
            if search_type == 'title':
                formatted_query = f'intitle:"{query}"'
            elif search_type == 'author':
                formatted_query = f'inauthor:"{query}"'
            elif search_type == 'publisher':
                formatted_query = f'inpublisher:"{query}"'
            elif search_type == 'subject':
                formatted_query = f'subject:"{query}"'
            elif search_type == 'isbn':
                formatted_query = f'isbn:{query}'

        # Calcular limite e início para paginação
        limit = items_per_page if items_per_page is not None else max_results
        start_index = (page - 1) * limit

        # Criar chave de cache
        cache_key = f"search_{self.context}_{formatted_query}_{limit}_{page}"
        cached_result = self.cache.get(cache_key)

        if cached_result:
            logger.info(f"[{self.context}] Usando resultado em cache para '{formatted_query}'")
            return cached_result

        # Preparar parâmetros
        params = {
            'q': formatted_query,
            'maxResults': limit,
            'startIndex': start_index,
            'printType': 'books',
            'langRestrict': 'pt',
        }

        if self.api_key:
            params['key'] = self.api_key

        try:
            # Fazer requisição
            response = requests.get(
                f"{self.base_url}/volumes",
                params=params,
                timeout=self.default_timeout
            )
            response.raise_for_status()

            data = response.json()

            # Processar resultados
            raw_books = data.get('items', [])
            total_items = data.get('totalItems', 0)

            # Transformar resultados
            books = []
            for book in raw_books:
                try:
                    volume_info = book.get('volumeInfo', {})

                    # Extrair e formatar informações
                    book_data = {
                        'id': book.get('id', ''),
                        'title': volume_info.get('title', 'Sem título'),
                        'subtitle': volume_info.get('subtitle', ''),
                        'authors': volume_info.get('authors', ['Autor desconhecido']),
                        'description': volume_info.get('description', 'Descrição não disponível'),
                        'published_date': volume_info.get('publishedDate', ''),
                        'publisher': volume_info.get('publisher', ''),
                        'categories': volume_info.get('categories', []),
                        'thumbnail': volume_info.get('imageLinks', {}).get('thumbnail', ''),
                        'language': volume_info.get('language', ''),
                        'page_count': volume_info.get('pageCount', 0),
                        'isbn': '',
                        'valor': 0,
                        'valor_promocional': 0
                    }

                    # Extrair ISBN
                    industry_identifiers = volume_info.get('industryIdentifiers', [])
                    for identifier in industry_identifiers:
                        if identifier.get('type') in ['ISBN_13', 'ISBN_10']:
                            book_data['isbn'] = identifier.get('identifier', '')
                            break

                    books.append(book_data)
                except Exception as e:
                    logger.error(f"[{self.context}] Erro ao processar livro: {str(e)}")

            # Calcular informações de paginação
            total_pages = max(1, (total_items + limit - 1) // limit)

            # Estrutura de resposta
            result = {
                'books': books,
                'total_pages': total_pages,
                'current_page': page,
                'has_previous': page > 1,
                'has_next': page < total_pages
            }

            # Armazenar no cache com tempo diferente para buscas
            self.cache.set(cache_key, result, timeout=SEARCH_CACHE_TIMEOUT)

            return result
        except Exception as e:
            logger.error(f"[{self.context}] Erro ao buscar na API: {str(e)}")
            return {
                'books': [],
                'total_pages': 1,
                'current_page': page,
                'has_previous': False,
                'has_next': False,
                'error': str(e)
            }

    def get_book_by_id(self, book_id: str) -> Optional[Dict[str, Any]]:
        """Obtém detalhes de um livro específico pelo ID"""
        # Chave de cache com contexto para evitar conflitos
        cache_key = f"book_{self.context}_{book_id}"
        cached_result = self.cache.get(cache_key)

        if cached_result:
            logger.info(f"[{self.context}] Usando dados em cache para livro ID '{book_id}'")
            return cached_result

        params = {}
        if self.api_key:
            params['key'] = self.api_key

        try:
            # Fazer requisição
            response = requests.get(
                f"{self.base_url}/volumes/{book_id}",
                params=params,
                timeout=self.default_timeout
            )
            response.raise_for_status()

            book_data = response.json()

            # Armazenar no cache
            self.cache.set(cache_key, book_data)

            return book_data
        except requests.RequestException as e:
            logger.error(f"[{self.context}] Erro ao obter livro ID '{book_id}': {str(e)}")
            return None

    # Métodos utilitários mantidos da implementação original

    def get_books_by_author(self, author: str, max_results: int = 10) -> Dict[str, Any]:
        """Busca livros de um autor específico"""
        query = f'inauthor:"{author}"'
        return self.search_books(query, max_results)

    def get_books_by_category(self, category: str, max_results: int = 10) -> Dict[str, Any]:
        """Busca livros de uma categoria específica"""
        query = f'subject:"{category}"'
        return self.search_books(query, max_results)

    def get_similar_books(self, book_title: str, author: str = None, max_results: int = 5) -> Dict[str, Any]:
        """Busca livros similares a um livro específico"""
        # Construir query baseada no título e autor (opcional)
        if author:
            query = f'intitle:"{book_title}" OR inauthor:"{author}"'
        else:
            query = f'intitle:"{book_title}"'

        return self.search_books(query, max_results)
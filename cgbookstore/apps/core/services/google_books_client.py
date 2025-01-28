"""
Módulo responsável pela comunicação com a API do Google Books.
Implementa cache e tratamento de erros.
"""
from typing import Optional, Dict, Any
import logging
import requests
from django.conf import settings
from django.core.cache import caches
from ..utils.google_books_cache import cache_google_books_api

logger = logging.getLogger(__name__)

class GoogleBooksClient:
    """Cliente para API do Google Books com cache integrado"""

    def __init__(self):
        self.api_key = settings.GOOGLE_BOOKS_API_KEY
        self.base_url = 'https://www.googleapis.com/books/v1/volumes'
        self.cache = caches['google_books']
        self._setup_logging()

    def _setup_logging(self):
        """Configura logging específico para o cliente"""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    @cache_google_books_api
    def search_books(self, query: str, search_type: str = 'all',
                    page: int = 1, items_per_page: int = 8) -> Dict[str, Any]:
        """
        Realiza busca de livros com cache.

        Args:
            query: Termo de busca
            search_type: Tipo de busca (all, title, author, category)
            page: Número da página
            items_per_page: Itens por página
        """
        try:
            # Construir query baseado no tipo de busca
            formatted_query = self._format_query(query, search_type)

            params = {
                'q': formatted_query,
                'key': self.api_key,
                'startIndex': (page - 1) * items_per_page,
                'maxResults': items_per_page
            }

            # Fazer requisição à API
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Criar um novo dicionário com apenas os dados serializáveis
            processed_data = self._process_search_response(data, page, items_per_page)
            return {
                'books': processed_data['books'],
                'total_pages': processed_data['total_pages'],
                'current_page': processed_data['current_page'],
                'has_next': processed_data['has_next'],
                'has_previous': processed_data['has_previous']
            }

        except requests.RequestException as e:
            self.logger.error(f"Erro na busca de livros: {str(e)}")
            return {
                'error': 'Erro ao buscar livros',
                'details': str(e),
                'books': [],
                'total_pages': 0,
                'current_page': page,
                'has_next': False,
                'has_previous': page > 1
            }

    def _format_query(self, query: str, search_type: str) -> str:
        """Formata a query baseada no tipo de busca"""
        if search_type == 'title':
            return f'intitle:{query}'
        elif search_type == 'author':
            return f'inauthor:{query}'
        elif search_type == 'category':
            return f'subject:{query}'
        return query

    def _process_search_response(self, data: Dict[str, Any],
                               page: int, items_per_page: int) -> Dict[str, Any]:
        """Processa a resposta da busca"""
        books = []
        for item in data.get('items', []):
            volume_info = item.get('volumeInfo', {})
            # log temporário
            if 'imageLinks' in volume_info:
                self.logger.info(f"Image links disponíveis: {volume_info['imageLinks']}")
            books.append({
                'id': item.get('id'),
                'title': volume_info.get('title', 'Título não disponível'),
                'authors': volume_info.get('authors', ['Autor desconhecido']),
                'description': volume_info.get('description', 'Descrição não disponível'),
                'published_date': volume_info.get('publishedDate', 'Data não disponível'),
                'thumbnail': volume_info.get('imageLinks', {}).get('extraLarge') or
                            volume_info.get('imageLinks', {}).get('large') or
                            volume_info.get('imageLinks', {}).get('medium') or
                            volume_info.get('imageLinks', {}).get('small') or
                            volume_info.get('imageLinks', {}).get('thumbnail', ''),
                'publisher': volume_info.get('publisher', ''),
                'categories': volume_info.get('categories', [])
            })

        total_items = data.get('totalItems', 0)
        total_pages = (total_items + items_per_page - 1) // items_per_page

        return {
            'books': books,
            'total_pages': total_pages,
            'current_page': page,
            'has_next': page < total_pages,
            'has_previous': page > 1
        }

    def _format_error_response(self, error_message: str) -> Dict[str, Any]:
        """Formata resposta de erro"""
        return {
            'error': 'Erro ao buscar livros',
            'details': error_message
        }
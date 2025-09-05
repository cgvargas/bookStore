# cgbookstore/apps/core/recommendations/services/google_books.py

import logging
from typing import List, Dict, Any, Set
from django.contrib.auth import get_user_model

# Reutilizaremos o seu cliente do Google Books já existente!
from ...services.google_books_service import GoogleBooksClient
from ...models import Book, UserBookShelf

logger = logging.getLogger(__name__)
User = get_user_model()


class GoogleBooksRecommendationService:
    """
    Serviço para encontrar recomendações de livros usando a API do Google Books.
    """

    def __init__(self, user: User):
        self.user = user
        self.client = GoogleBooksClient(context="recommendations")

    def get_recommendations(self, seed_books: List[Book], limit: int) -> List[Dict[str, Any]]:
        """
        Gera recomendações externas com base nos livros-semente.
        """
        if not seed_books or limit <= 0:
            return []

        # 1. Criar termos de busca a partir dos livros-semente
        #    Usaremos uma combinação de autores e gêneros para diversificar a busca.
        search_terms = self._generate_search_terms(seed_books)

        # 2. Obter a lista de todos os títulos que o usuário já possui para evitar duplicatas
        user_library_titles = {
            shelf.book.titulo.lower()
            for shelf in UserBookShelf.objects.filter(user=self.user).select_related('book')
        }

        # 3. Buscar na API e coletar os resultados
        recommended_books = []
        seen_external_ids = set()

        for term in search_terms:
            if len(recommended_books) >= limit:
                break

            try:
                results = self.client.search_books(term, max_results=5)
                for book_data in results:
                    if len(recommended_books) >= limit:
                        break

                    external_id = book_data.get('id')
                    title = book_data.get('volumeInfo', {}).get('title', '').lower()

                    # Verificar se o livro já foi recomendado ou se o usuário já o tem
                    if external_id not in seen_external_ids and title not in user_library_titles:
                        recommended_books.append(book_data)
                        seen_external_ids.add(external_id)

            except Exception as e:
                logger.error(f"Erro ao buscar termo '{term}' na API do Google Books: {e}")
                continue

        return recommended_books

    def _generate_search_terms(self, seed_books: List[Book]) -> List[str]:
        """Gera uma lista de termos de busca a partir dos livros-semente."""
        terms = set()

        # Adiciona termos de autores
        for book in seed_books:
            if book.autor:
                terms.add(f"inauthor:{book.autor}")

        # Adiciona termos de gêneros
        for book in seed_books:
            if book.genero:
                terms.add(f"subject:{book.genero}")

        # Limita o número de termos para não sobrecarregar a API
        return list(terms)[:10]
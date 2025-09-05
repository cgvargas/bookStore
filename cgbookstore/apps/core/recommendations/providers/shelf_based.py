# cgbookstore/apps/core/recommendations/providers/shelf_based.py

from typing import List
from django.contrib.auth import get_user_model
from ...models import UserBookShelf, Book

User = get_user_model()


def get_seed_books_from_shelves(user: User, limit: int = 50) -> List[Book]:
    """
    Coleta uma lista de livros das prateleiras do usuário para usar como
    base para as recomendações, seguindo uma ordem de prioridade.

    Prioridade: Favoritos > Lidos > Lendo > Vou Ler.
    """

    # Ordem de prioridade das prateleiras
    shelf_priority = ['favorito', 'lido', 'lendo', 'vou_ler']

    seed_books = []
    seen_book_ids = set()

    for shelf_type in shelf_priority:
        # Busca os livros para o tipo de prateleira atual
        shelves = UserBookShelf.objects.filter(
            user=user,
            shelf_type=shelf_type,
            book__is_temporary=False  # Ignora livros temporários/externos
        ).select_related('book').order_by('-added_at')

        for shelf in shelves:
            if shelf.book and shelf.book.id not in seen_book_ids:
                seed_books.append(shelf.book)
                seen_book_ids.add(shelf.book.id)

                # Para de coletar se atingir o limite
                if len(seed_books) >= limit:
                    return seed_books

    return seed_books
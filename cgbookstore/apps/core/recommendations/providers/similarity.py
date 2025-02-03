from django.db.models import Q, Count
from django.db.models.functions import Random
from ...models import Book, User, UserBookShelf
from ..utils.processors import SimilarityProcessor


class SimilarityBasedProvider:
    """Provider de recomendações baseadas em similaridade entre livros"""

    def __init__(self):
        self._processor = SimilarityProcessor()

    def get_recommendations(self, user: User, limit: int = 20):
        """
        Gera recomendações baseadas em similaridade
        Args:
            user: Usuário alvo
            limit: Limite de recomendações
        Returns:
            QuerySet com livros recomendados
        """
        # Obtém livros favoritos do usuário
        favorite_books = self._get_user_favorites(user)

        if not favorite_books:
            return Book.objects.all().order_by(Random())[:limit]

        # Calcula similaridade e obtém recomendações
        similar_books = self._find_similar_books(favorite_books)

        # Exclui livros já lidos
        recommendations = similar_books.exclude(
            id__in=self._get_read_books(user)
        )[:limit]

        return recommendations

    def _get_user_favorites(self, user: User):
        """
        Obtém livros favoritos do usuário
        Args:
            user: Usuário alvo
        Returns:
            QuerySet com livros favoritos
        """
        return UserBookShelf.objects.filter(
            user=user,
            shelf_type='favorito'
        ).select_related('book')

    def _find_similar_books(self, favorite_books):
        """
        Encontra livros similares aos favoritos
        Args:
            favorite_books: QuerySet com livros favoritos
        Returns:
            QuerySet com livros similares
        """
        similarity_criteria = Q()

        for shelf in favorite_books:
            book = shelf.book

            # Constrói query baseada em múltiplos critérios
            book_criteria = (
                    Q(autor=book.autor) |
                    Q(genero=book.genero) |
                    Q(categoria=book.categoria)
            )

            similarity_criteria |= book_criteria

        return Book.objects.filter(similarity_criteria).distinct()

    def _get_read_books(self, user: User):
        """
        Obtém IDs dos livros já lidos pelo usuário
        Args:
            user: Usuário alvo
        Returns:
            Lista de IDs
        """
        return UserBookShelf.objects.filter(
            user=user
        ).values_list('book', flat=True)

    def calculate_similarity_score(self, book1: Book, book2: Book) -> float:
        """
        Calcula score de similaridade entre dois livros
        Args:
            book1: Primeiro livro
            book2: Segundo livro
        Returns:
            Score de similaridade (0-1)
        """
        return self._processor.calculate_similarity(book1, book2)
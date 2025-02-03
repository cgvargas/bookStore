from typing import List, Dict
from django.db.models import QuerySet
from django.contrib.auth import get_user_model
from ..models import Book, UserBookShelf
from .providers.history import HistoryBasedProvider
from .providers.category import CategoryBasedProvider
from .providers.similarity import SimilarityBasedProvider
from .services.calculator import RecommendationCalculator

User = get_user_model()


class RecommendationEngine:
    """Motor principal do sistema de recomendações"""

    def __init__(self):
        self._history_provider = HistoryBasedProvider()
        self._category_provider = CategoryBasedProvider()
        self._similarity_provider = SimilarityBasedProvider()
        self._calculator = RecommendationCalculator()

    def get_recommendations(self, user: User, limit: int = 10) -> QuerySet[Book]:
        """
        Obtém recomendações personalizadas para um usuário
        Args:
            user: Usuário para qual gerar recomendações
            limit: Número máximo de recomendações
        Returns:
            QuerySet com os livros recomendados
        """
        # Obtém IDs dos livros já lidos
        read_books = UserBookShelf.objects.filter(
            user=user,
            shelf_type='lido'
        ).values_list('book_id', flat=True)

        # Coleta recomendações de cada provider
        history_recs = self._history_provider.get_recommendations(user)
        category_recs = self._category_provider.get_recommendations(user)
        similarity_recs = self._similarity_provider.get_recommendations(user)

        # Combina e calcula scores
        all_recommendations = {
            'history': history_recs,
            'category': category_recs,
            'similarity': similarity_recs
        }

        scores = self._calculator.calculate_scores(all_recommendations)

        # Obtém os IDs dos livros mais bem pontuados
        top_book_ids = sorted(
            scores.keys(),
            key=lambda x: scores[x],
            reverse=True
        )[:limit]

        # Retorna QuerySet com os livros, excluindo os já lidos
        return Book.objects.filter(id__in=top_book_ids).exclude(id__in=read_books)

    def get_personalized_shelf(self, user: User, shelf_size: int = 5) -> Dict:
        """
        Cria uma prateleira personalizada com diferentes tipos de recomendações
        Args:
            user: Usuário alvo
            shelf_size: Tamanho de cada seção
        Returns:
            Dicionário com diferentes categorias de recomendações
        """
        # Obtém IDs dos livros já lidos
        read_books = UserBookShelf.objects.filter(
            user=user,
            shelf_type='lido'
        ).values_list('book_id', flat=True)

        return {
            'based_on_history': self._history_provider.get_recommendations(user)[:shelf_size],
            'based_on_categories': self._category_provider.get_recommendations(user)[:shelf_size],
            'you_might_like': self._similarity_provider.get_recommendations(user)[:shelf_size]
        }
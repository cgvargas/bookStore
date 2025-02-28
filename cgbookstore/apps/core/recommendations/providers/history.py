from typing import List, Dict
from django.db.models import QuerySet, Count, Q, F, Value, FloatField
from django.db.models.functions import Cast
from django.utils import timezone
from ...models import Book, User, UserBookShelf
from django.contrib.auth import get_user_model
from ..providers.exclusion import ExclusionProvider

User = get_user_model()


class HistoryBasedProvider:
    """Provider de recomendações baseadas em histórico de leitura"""

    SHELF_WEIGHTS = {
        'favorito': 3.0,
        'lido': 1.5,
        'lendo': 1.0,
        'vou_ler': 0.5,
        'abandonei': 0.5
    }

    def get_recommendations(self, user: User, limit: int = 20) -> QuerySet:
        """
        Gera recomendações baseadas no histórico de leitura do usuário
        """
        excluded_books = ExclusionProvider.get_excluded_books(user)
        reading_history = self._get_reading_history(user)

        if not reading_history:
            return Book.objects.none()

        patterns = self._analyze_reading_patterns(reading_history)
        query = self._build_recommendation_query(patterns)

        if not query:
            return Book.objects.none()

        recommendations = self._apply_recommendation_filters(query, excluded_books, limit)
        return recommendations

    def _get_reading_history(self, user: User) -> List[UserBookShelf]:
        """Obtém histórico de leitura com pesos por tipo de prateleira"""
        history = list(UserBookShelf.objects.filter(
            user=user,
            shelf_type__in=self.SHELF_WEIGHTS.keys()
        ).select_related('book').order_by('-added_at'))

        # Adiciona pesos manualmente após a query
        for item in history:
            item.weight = self.SHELF_WEIGHTS.get(item.shelf_type, 1.0)

        return history

    def _analyze_reading_patterns(self, reading_history: List[UserBookShelf]) -> Dict:
        """Analisa padrões com pesos por relevância e tempo"""
        now = timezone.now()
        patterns = {
            'authors': {},
            'genres': {},
            'categories': {},
            'themes': set()
        }

        for shelf in reading_history:
            time_diff = (now - shelf.added_at).days
            time_weight = 1.0 / (1 + time_diff / 30)
            total_weight = time_weight * self.SHELF_WEIGHTS.get(shelf.shelf_type, 1.0)

            book = shelf.book

            if book.autor:
                patterns['authors'][book.autor] = patterns['authors'].get(
                    book.autor, 0) + total_weight

            if book.genero:
                patterns['genres'][book.genero] = patterns['genres'].get(
                    book.genero, 0) + total_weight

            if book.categoria:
                patterns['categories'][book.categoria] = patterns['categories'].get(
                    book.categoria, 0) + total_weight

            if book.temas:
                themes = set(t.strip() for t in book.temas.split(','))
                patterns['themes'].update(themes)

        return self._normalize_patterns(patterns)

    def _normalize_patterns(self, patterns: Dict) -> Dict:
        """Normaliza os pesos para valores entre 0 e 1"""
        for key in ['authors', 'genres', 'categories']:
            if patterns[key]:
                max_weight = max(patterns[key].values())
                if max_weight > 0:
                    patterns[key] = {
                        k: v / max_weight for k, v in patterns[key].items()
                    }
        return patterns

    def _build_recommendation_query(self, patterns: Dict) -> Q:
        """Constrói query baseada nos padrões analisados"""
        query = Q()
        weight_threshold = 0.5

        # Autores relevantes
        authors = [k for k, v in patterns['authors'].items() if v > weight_threshold]
        if authors:
            query |= Q(autor__in=authors)

        # Gêneros relevantes
        genres = [k for k, v in patterns['genres'].items() if v > weight_threshold]
        if genres:
            query |= Q(genero__in=genres)

        # Categorias relevantes
        categories = [k for k, v in patterns['categories'].items() if v > weight_threshold]
        if categories:
            query |= Q(categoria__in=categories)

        # Temas
        if patterns['themes']:
            theme_query = Q()
            for theme in patterns['themes']:
                theme_query |= Q(temas__icontains=theme)
            query |= theme_query

        return query

    def _apply_recommendation_filters(
            self, query: Q, excluded_books: set, limit: int
    ) -> QuerySet:
        """Aplica filtros finais e retorna recomendações"""
        return Book.objects.filter(query).exclude(
            id__in=excluded_books
        ).distinct().order_by('?')[:limit]

    def get_reading_patterns(self, user: User) -> Dict:
        """Retorna padrões de leitura para análise externa"""
        reading_history = self._get_reading_history(user)
        return self._analyze_reading_patterns(reading_history)
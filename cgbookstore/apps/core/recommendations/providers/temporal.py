from typing import Dict, List, Set
from django.db.models import QuerySet, Count, Q, F
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from ...models import Book, UserBookShelf
from ..providers.exclusion import ExclusionProvider

User = get_user_model()


class SeasonalAnalyzer:
    """Analisador de padrões de leitura sazonais"""

    SEASONS = {
        'verao': [12, 1, 2],
        'outono': [3, 4, 5],
        'inverno': [6, 7, 8],
        'primavera': [9, 10, 11]
    }

    WEIGHTS = {
        'current': 1.0,
        'previous': 0.7,
        'next': 0.5
    }

    def get_current_season(self) -> str:
        current_month = timezone.now().month
        return next(
            season for season, months in self.SEASONS.items()
            if current_month in months
        )

    def get_adjacent_seasons(self, current_season: str) -> tuple:
        seasons = list(self.SEASONS.keys())
        current_idx = seasons.index(current_season)
        previous = seasons[(current_idx - 1) % 4]
        next_season = seasons[(current_idx + 1) % 4]
        return previous, next_season

    def analyze_seasonal_patterns(self, reading_history: QuerySet) -> Dict:
        current_season = self.get_current_season()
        previous_season, next_season = self.get_adjacent_seasons(current_season)

        patterns = {
            season: {'genres': {}, 'categories': {}}
            for season in [current_season, previous_season, next_season]
        }

        for shelf in reading_history:
            month = shelf.added_at.month
            season = next(
                season for season, months in self.SEASONS.items()
                if month in months
            )

            if season not in patterns:
                continue

            weight = self.WEIGHTS.get(
                'current' if season == current_season else
                'previous' if season == previous_season else
                'next'
            )

            book = shelf.book
            if book.genero:
                patterns[season]['genres'][book.genero] = \
                    patterns[season]['genres'].get(book.genero, 0) + weight
            if book.categoria:
                patterns[season]['categories'][book.categoria] = \
                    patterns[season]['categories'].get(book.categoria, 0) + weight

        return patterns


class RollingAnalyzer:
    """Analisador de padrões de leitura em períodos móveis"""

    PERIODS = {
        'last_30d': {'days': 30, 'weight': 1.0},
        'last_60d': {'days': 60, 'weight': 0.7},
        'last_90d': {'days': 90, 'weight': 0.5}
    }

    def analyze_rolling_patterns(self, reading_history: QuerySet) -> Dict:
        now = timezone.now()
        patterns = {
            period: {'genres': {}, 'categories': {}}
            for period in self.PERIODS.keys()
        }

        for shelf in reading_history:
            days_ago = (now - shelf.added_at).days
            book = shelf.book

            for period, config in self.PERIODS.items():
                if days_ago <= config['days']:
                    if book.genero:
                        patterns[period]['genres'][book.genero] = \
                            patterns[period]['genres'].get(book.genero, 0) + config['weight']
                    if book.categoria:
                        patterns[period]['categories'][book.categoria] = \
                            patterns[period]['categories'].get(book.categoria, 0) + config['weight']

        return patterns


class TemporalProvider:
    """Provider de recomendações baseadas em análise temporal"""

    def __init__(self):
        self.seasonal_analyzer = SeasonalAnalyzer()
        self.rolling_analyzer = RollingAnalyzer()

    def get_recommendations(self, user: User, limit: int = 20) -> QuerySet:
        excluded_books = ExclusionProvider.get_excluded_books(user)
        reading_history = self._get_reading_history(user)

        if not reading_history.exists():
            return Book.objects.none()

        query = self._build_temporal_query(reading_history)

        if not query:
            return Book.objects.none()

        return self._apply_recommendation_filters(query, excluded_books, limit)

    def _get_reading_history(self, user: User) -> QuerySet:
        """Obtém histórico de leitura para análise temporal"""
        return UserBookShelf.objects.filter(
            user=user,
            shelf_type__in=['lido', 'lendo', 'favorito']
        ).select_related('book').order_by('-added_at')

    def _build_temporal_query(self, reading_history: QuerySet) -> Q:
        """Constrói query combinando padrões sazonais e móveis"""
        seasonal_patterns = self.seasonal_analyzer.analyze_seasonal_patterns(reading_history)
        rolling_patterns = self.rolling_analyzer.analyze_rolling_patterns(reading_history)

        current_season = self.seasonal_analyzer.get_current_season()

        query = Q()

        # Processa padrões sazonais
        if seasonal_patterns.get(current_season):
            seasonal_data = seasonal_patterns[current_season]

            if seasonal_data['genres']:
                top_genres = sorted(
                    seasonal_data['genres'].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:3]
                query |= Q(genero__in=[g[0] for g in top_genres])

            if seasonal_data['categories']:
                top_categories = sorted(
                    seasonal_data['categories'].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:3]
                query |= Q(categoria__in=[c[0] for c in top_categories])

        # Processa padrões móveis do período mais recente
        recent_data = rolling_patterns.get('last_30d', {})
        if recent_data:
            if recent_data['genres']:
                top_recent_genres = sorted(
                    recent_data['genres'].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:3]
                query |= Q(genero__in=[g[0] for g in top_recent_genres])

            if recent_data['categories']:
                top_recent_categories = sorted(
                    recent_data['categories'].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:3]
                query |= Q(categoria__in=[c[0] for c in top_recent_categories])

        return query

    def _apply_recommendation_filters(
            self, query: Q, excluded_books: set, limit: int
    ) -> QuerySet:
        """Aplica filtros finais e retorna recomendações"""
        return Book.objects.filter(query).exclude(
            id__in=excluded_books
        ).distinct().order_by('?')[:limit]

    def get_temporal_patterns(self, user: User) -> Dict:
        """Retorna padrões temporais para análise externa"""
        reading_history = self._get_reading_history(user)

        return {
            'seasonal': self.seasonal_analyzer.analyze_seasonal_patterns(reading_history),
            'rolling': self.rolling_analyzer.analyze_rolling_patterns(reading_history)
        }
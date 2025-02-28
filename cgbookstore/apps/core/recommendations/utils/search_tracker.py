import json
from datetime import datetime, timedelta
from django.core.cache import cache
from django.contrib.auth import get_user_model

User = get_user_model()


class SearchTracker:
    """Gerenciador de histórico de buscas do usuário"""

    CACHE_TTL = 60 * 60 * 24 * 30  # 30 dias
    CACHE_KEY_PREFIX = 'user_search_history_'

    @staticmethod
    def _get_cache_key(user_id: int) -> str:
        """Gera chave de cache para o usuário"""
        return f"{SearchTracker.CACHE_KEY_PREFIX}{user_id}"

    @staticmethod
    def add_search(user: User, search_term: str, clicked_books: list = None):
        """
        Registra uma nova busca do usuário
        Args:
            user: Usuário que realizou a busca
            search_term: Termo pesquisado
            clicked_books: Lista de IDs dos livros clicados nos resultados
        """
        cache_key = SearchTracker._get_cache_key(user.id)
        current_history = cache.get(cache_key) or []

        # Cria novo registro de busca
        search_record = {
            'term': search_term,
            'timestamp': datetime.now().isoformat(),
            'clicked_books': clicked_books or []
        }

        # Adiciona no início da lista
        current_history.insert(0, search_record)

        # Mantém apenas últimos 30 dias
        cutoff_date = datetime.now() - timedelta(days=30)
        filtered_history = [
            record for record in current_history
            if datetime.fromisoformat(record['timestamp']) > cutoff_date
        ]

        # Atualiza cache
        cache.set(cache_key, filtered_history, SearchTracker.CACHE_TTL)

    @staticmethod
    def get_recent_searches(user: User, days: int = 30) -> list:
        """
        Obtém buscas recentes do usuário
        Args:
            user: Usuário alvo
            days: Número de dias para considerar
        Returns:
            Lista com histórico de buscas
        """
        cache_key = SearchTracker._get_cache_key(user.id)
        history = cache.get(cache_key) or []

        if not days:
            return history

        cutoff_date = datetime.now() - timedelta(days=days)
        return [
            record for record in history
            if datetime.fromisoformat(record['timestamp']) > cutoff_date
        ]

    @staticmethod
    def get_search_patterns(user: User) -> dict:
        """
        Analisa padrões nas buscas do usuário
        Args:
            user: Usuário alvo
        Returns:
            Dicionário com análise dos padrões
        """
        history = SearchTracker.get_recent_searches(user)

        patterns = {
            'common_terms': {},
            'clicked_books': set(),
            'search_frequency': {}
        }

        for record in history:
            # Analisa termos comuns
            terms = record['term'].lower().split()
            for term in terms:
                patterns['common_terms'][term] = \
                    patterns['common_terms'].get(term, 0) + 1

            # Registra livros clicados
            patterns['clicked_books'].update(record['clicked_books'])

            # Analisa frequência por dia
            day = datetime.fromisoformat(record['timestamp']).strftime('%Y-%m-%d')
            patterns['search_frequency'][day] = \
                patterns['search_frequency'].get(day, 0) + 1

        return patterns
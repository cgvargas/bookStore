from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from datetime import datetime, timedelta
from ..utils.search_tracker import SearchTracker

User = get_user_model()


class SearchTrackerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        # Limpa cache antes dos testes
        cache.clear()

    def test_add_search(self):
        """Testa adição de nova busca"""
        SearchTracker.add_search(
            self.user,
            'python programming',
            clicked_books=[1, 2, 3]
        )

        history = SearchTracker.get_recent_searches(self.user)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['term'], 'python programming')
        self.assertEqual(history[0]['clicked_books'], [1, 2, 3])

    def test_get_recent_searches(self):
        """Testa obtenção de buscas recentes"""
        # Adiciona buscas com datas diferentes
        old_date = (datetime.now() - timedelta(days=40)).isoformat()
        recent_date = (datetime.now() - timedelta(days=5)).isoformat()

        cache_key = SearchTracker._get_cache_key(self.user.id)
        cache.set(cache_key, [
            {'term': 'old search', 'timestamp': old_date, 'clicked_books': []},
            {'term': 'recent search', 'timestamp': recent_date, 'clicked_books': []}
        ])

        # Testa filtro por dias
        recent = SearchTracker.get_recent_searches(self.user, days=30)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0]['term'], 'recent search')

    def test_get_search_patterns(self):
        """Testa análise de padrões de busca"""
        SearchTracker.add_search(
            self.user,
            'python programming',
            clicked_books=[1]
        )
        SearchTracker.add_search(
            self.user,
            'python books',
            clicked_books=[2]
        )

        patterns = SearchTracker.get_search_patterns(self.user)

        self.assertIn('python', patterns['common_terms'])
        self.assertEqual(patterns['common_terms']['python'], 2)
        self.assertEqual(len(patterns['clicked_books']), 2)
        self.assertEqual(len(patterns['search_frequency']), 1)  # Mesmo dia
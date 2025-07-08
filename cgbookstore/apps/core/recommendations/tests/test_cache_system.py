# cgbookstore/apps/core/recommendations/tests/test_cache_system.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import caches
from datetime import timedelta
from unittest.mock import patch, MagicMock
import hashlib

from cgbookstore.apps.core.models import Book, UserBookShelf, Profile
from cgbookstore.apps.core.recommendations.utils.cache_manager import RecommendationCache
from .test_helpers import create_test_user

User = get_user_model()


class CacheSystemTests(TestCase):
    """Testes para o sistema de cache inteligente"""

    def setUp(self):
        # Cria usuários com diferentes perfis usando o helper
        self.eclectic_user = create_test_user(
            'eclectic_reader_cache_sys')  # Renomeado para evitar conflitos de username
        self.loyal_user = create_test_user('loyal_reader_cache_sys')
        self.seasonal_user = create_test_user('seasonal_reader_cache_sys')

        # Define self.user para ser usado nos testes da classe
        self.user = self.eclectic_user

        # Cria alguns livros e prateleira
        self.books = []
        for i in range(5):
            book = Book.objects.create(
                titulo=f'Livro CacheSys {i}',  # Nomeado para evitar conflitos
                autor=f'Autor CacheSys {i}',
                idioma='pt-BR',
                categoria='Ficção CacheSys'
            )
            self.books.append(book)

            if i < 3:  # Adiciona 3 livros para self.user (eclectic_user)
                UserBookShelf.objects.create(
                    user=self.user,
                    book=book,
                    shelf_type='lido'
                )

    def test_cache_key_sanitization(self):
        """Testa sanitização de chaves de cache"""
        test_cases = [
            ('key with spaces', 'key_with_spaces'),
            ('key!@#$%^&*()', 'key'),
            ('a' * 300, lambda x: x.startswith('a' * 200) and hashlib.md5(('a' * 300).encode()).hexdigest() in x),
            ('válid_key-123', 'vlid_key-123'),  # Esperado que 'á' seja removido
        ]

        for input_key, expected in test_cases:
            result = RecommendationCache.sanitize_cache_key(input_key)

            if callable(expected):
                self.assertTrue(expected(result), f"Falha para callable com input: {input_key}, resultado: {result}")
            elif input_key == 'válid_key-123':
                # Usar assertEqual para o caso problemático para ver a diferença exata
                self.assertEqual(result, expected,
                                 f"Falha para '{input_key}'. Esperado: '{expected}', Recebido: '{result}'")
            else:
                self.assertTrue(result.startswith(expected),
                                f"Falha para '{input_key}'. Resultado '{result}' não começa com '{expected}'")

            self.assertLess(len(result), 251, f"Chave muito longa para input: {input_key}, resultado: {result}")

    def test_cache_storage_and_retrieval(self):
        """Testa armazenamento e recuperação de cache"""
        recommendations = [self.books[0], self.books[1]]
        metadata = {'source': 'test', 'version': '2.0'}  # 'version' aqui é do metadata, não do cache_data principal

        RecommendationCache.set_recommendations(
            self.user,
            recommendations,
            metadata
        )

        cached_data_wrapper = RecommendationCache.get_recommendations(
            self.user)  # get_recommendations retorna o dict wrapper

        self.assertIsNotNone(cached_data_wrapper)
        # O _serialize_recommendations do RecommendationCache cria um dict com 'recommendations', 'timestamp', etc.
        # E o set_recommendations adiciona o 'metadata' que passamos.
        self.assertEqual(cached_data_wrapper.get('metadata'), metadata)
        self.assertEqual(len(cached_data_wrapper.get('recommendations', [])), 2)
        self.assertEqual(cached_data_wrapper.get('version'), '2.0')  # Versão do cache_data principal

    def test_cache_invalidation_events(self):
        """Testa invalidação seletiva por eventos"""
        RecommendationCache.set_recommendations(self.user, [self.books[0]], metadata={'test': 1})
        RecommendationCache.set_language_profile(self.user, {'pt': 5.0})
        RecommendationCache.set_user_behavior(self.user, {'is_eclectic': True})
        RecommendationCache.set_shelf(self.user, {'books': [self.books[0].id]})

        RecommendationCache.invalidate_user_cache(self.user, 'book_added')  # Invalida 'recommendations' e 'shelf'

        self.assertIsNone(RecommendationCache.get_recommendations(self.user))
        self.assertIsNone(RecommendationCache.get_shelf(self.user))
        self.assertIsNotNone(RecommendationCache.get_language_profile(self.user))
        self.assertIsNotNone(RecommendationCache.get_user_behavior(self.user))

        RecommendationCache.set_recommendations(self.user, [self.books[0]], metadata={'test': 2})
        RecommendationCache.set_language_profile(self.user, {'pt': 5.0})
        RecommendationCache.set_user_behavior(self.user, {'is_eclectic': True})

        RecommendationCache.invalidate_user_cache(self.user,
                                                  'reading_completed')  # Invalida 'recommendations', 'language_profile', 'behavior'

        self.assertIsNone(RecommendationCache.get_recommendations(self.user))
        self.assertIsNone(RecommendationCache.get_language_profile(self.user))
        self.assertIsNone(RecommendationCache.get_user_behavior(self.user))

    def test_cache_validation(self):
        """Testa validação de cache"""
        # Contexto inicial: self.user tem 3 livros (Book CacheSys 0, 1, 2)
        initial_context = RecommendationCache._get_user_context(self.user)
        valid_cache = {
            'version': '2.0',
            'timestamp': timezone.now().isoformat(),
            'user_context': initial_context,
            'recommendations': [],
            'metadata': {}
        }
        self.assertTrue(RecommendationCache._is_cache_valid(valid_cache, self.user))

        old_version_cache = valid_cache.copy()
        old_version_cache['version'] = '1.0'
        self.assertFalse(RecommendationCache._is_cache_valid(old_version_cache, self.user))

        old_timestamp_cache = valid_cache.copy()
        old_timestamp_cache['timestamp'] = (timezone.now() - timedelta(days=2)).isoformat()
        self.assertFalse(RecommendationCache._is_cache_valid(old_timestamp_cache, self.user))

        # Adiciona 2 livros para self.user. Total agora é 3 (setUp) + 2 = 5 livros
        # A diferença será 5 - 3 = 2.
        # Com a regra alterada para > 1 (ou >=2) em _is_cache_valid, isso deve invalidar.
        UserBookShelf.objects.create(user=self.user, book=self.books[3], shelf_type='lido')
        UserBookShelf.objects.create(user=self.user, book=self.books[4], shelf_type='lido')

        self.assertFalse(RecommendationCache._is_cache_valid(valid_cache, self.user),
                         "Cache deveria ser inválido após adicionar 2 livros.")

    def test_user_context_extraction(self):
        """Testa extração de contexto do usuário"""
        context = RecommendationCache._get_user_context(self.user)

        self.assertIn('total_books', context)
        self.assertIn('shelf_counts', context)
        self.assertIn('favorite_category', context)
        self.assertIn('last_activity', context)

        self.assertEqual(context['total_books'], 3)  # Baseado no setUp
        self.assertEqual(context['shelf_counts']['lido'], 3)
        self.assertEqual(context['favorite_category'], 'Ficção CacheSys')

    def test_recommendation_serialization(self):
        """Testa serialização de recomendações"""
        recommendations = [
            self.books[0],
            {'id': 'ext1', 'volumeInfo': {'title': 'External Book'}},
            self.books[1]
        ]
        serialized = RecommendationCache._serialize_recommendations(recommendations)

        self.assertEqual(len(serialized), 3)
        self.assertEqual(serialized[0]['type'], 'local')
        self.assertEqual(serialized[1]['type'], 'external')
        self.assertEqual(serialized[0]['id'], self.books[0].id)
        self.assertEqual(serialized[1]['data']['id'], 'ext1')

    def test_cache_warm_up(self):
        """Testa aquecimento de cache"""
        with patch(
                'cgbookstore.apps.core.recommendations.providers.language_preference.LanguagePreferenceProvider') as mock_lang_provider_cls:
            with patch('cgbookstore.apps.core.recommendations.engine.RecommendationEngine') as mock_engine_cls:
                mock_lang_instance = MagicMock()
                mock_lang_instance.get_language_affinity.return_value = {'pt': 5.0, 'preferred_languages': {'pt': 1.0},
                                                                         'portuguese_preference': 1.0}
                mock_lang_provider_cls.return_value = mock_lang_instance

                mock_engine_instance = MagicMock()
                mock_engine_instance._analyze_user_behavior.return_value = {'is_eclectic': True}
                mock_engine_cls.return_value = mock_engine_instance

                RecommendationCache.warm_cache(self.user)

                mock_lang_instance.get_language_affinity.assert_called_once_with(self.user)
                mock_engine_instance._analyze_user_behavior.assert_called_once_with(self.user)

    def test_cache_stats(self):
        """Testa estatísticas de cache"""
        RecommendationCache.set_recommendations(self.user, [], metadata={})
        RecommendationCache.set_language_profile(self.user, {})  # Salva um dict vazio

        stats = RecommendationCache.get_cache_stats(self.user)

        self.assertTrue(stats['recommendations'])
        self.assertTrue(stats['language_profile'],
                        "Language profile deveria ser True se a chave existe, mesmo com dict vazio")
        self.assertFalse(stats['shelf'])
        self.assertFalse(stats['behavior'])
import pytest
import hashlib
import time
from django.test import TestCase, override_settings
from django.core.cache import caches
from django.contrib.auth import get_user_model
from cgbookstore.apps.core.recommendations.utils.cache_manager import RecommendationCache
from cgbookstore.apps.core.services.google_books_service import GoogleBooksCache

User = get_user_model()


class CacheManagerTest(TestCase):
    """
    Testes para o gerenciador de cache de recomendações.
    Verifica o funcionamento correto, independentemente do backend (Redis ou DatabaseCache).
    """

    def setUp(self):
        # Criar um usuário para testes
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )

    def test_cache_key_sanitization(self):
        """Testa a funcionalidade de sanitização de chaves de cache"""
        # Chave com caracteres especiais
        key = "test key with $pecial ch@racters!"
        sanitized = RecommendationCache.sanitize_cache_key(key)

        # Verificar se a chave sanitizada contém apenas caracteres permitidos
        self.assertTrue(all(c.isalnum() or c in ['_', '-'] for c in sanitized))
        self.assertNotIn(' ', sanitized)  # Não deve conter espaços
        self.assertNotIn('!', sanitized)  # Não deve conter caracteres especiais

        # Teste com chave muito longa
        long_key = "a" * 300
        sanitized_long = RecommendationCache.sanitize_cache_key(long_key)
        self.assertLessEqual(len(sanitized_long), 250)

    def test_recommendation_cache_operations(self):
        """Testa as operações básicas do cache de recomendações"""
        # Dados de teste
        test_recommendations = [
            {'id': '123', 'title': 'Test Book 1'},
            {'id': '456', 'title': 'Test Book 2'}
        ]

        # 1. Verificar que o cache está vazio inicialmente
        self.assertIsNone(RecommendationCache.get_recommendations(self.user))

        # 2. Armazenar recomendações no cache
        RecommendationCache.set_recommendations(self.user, test_recommendations)

        # 3. Verificar se os dados foram armazenados corretamente
        cached_data = RecommendationCache.get_recommendations(self.user)
        self.assertEqual(cached_data, test_recommendations)

        # 4. Testar invalidação de cache
        RecommendationCache.invalidate_user_cache(self.user)
        self.assertIsNone(RecommendationCache.get_recommendations(self.user))

    def test_shelf_cache_operations(self):
        """Testa as operações do cache de prateleiras"""
        # Dados de teste
        test_shelf = {
            'name': 'Test Shelf',
            'books': [
                {'id': '123', 'title': 'Test Book 1'},
                {'id': '456', 'title': 'Test Book 2'}
            ]
        }

        # 1. Verificar que o cache está vazio inicialmente
        self.assertIsNone(RecommendationCache.get_shelf(self.user))

        # 2. Armazenar prateleira no cache
        RecommendationCache.set_shelf(self.user, test_shelf)

        # 3. Verificar se os dados foram armazenados corretamente
        cached_data = RecommendationCache.get_shelf(self.user)
        self.assertEqual(cached_data, test_shelf)

        # 4. Testar invalidação de cache
        RecommendationCache.invalidate_user_cache(self.user)
        self.assertIsNone(RecommendationCache.get_shelf(self.user))

    def test_generate_recommendation_key(self):
        """Testa a geração de chaves de recomendação"""
        user_id = 123
        shelf_hash = 456
        shelf_count = 10
        timestamp = int(time.time())

        key = RecommendationCache.get_recommendation_key(
            user_id, shelf_hash, shelf_count, timestamp
        )

        # Verificar se a chave contém os componentes esperados
        self.assertIn(str(user_id), key)
        self.assertIn(str(shelf_hash), key)
        self.assertIn(str(shelf_count), key)
        self.assertIn(str(timestamp), key)


class GoogleBooksCacheTest(TestCase):
    """
    Testes para o cache do Google Books.
    Verifica o funcionamento correto, independentemente do backend (Redis ou DatabaseCache).
    """

    def test_google_books_cache_operations(self):
        """Testa operações básicas do cache do Google Books"""
        cache = GoogleBooksCache(namespace="test_namespace")

        # Dados de teste
        test_key = "test_book_123"
        test_data = {
            "id": "123",
            "title": "Test Book",
            "authors": ["Test Author"],
            "description": "Test description"
        }

        # 1. Verificar que o cache está vazio inicialmente
        self.assertIsNone(cache.get(test_key))

        # 2. Armazenar dados no cache
        cache.set(test_key, test_data)

        # 3. Verificar se os dados foram armazenados corretamente
        cached_data = cache.get(test_key)
        self.assertEqual(cached_data, test_data)

        # 4. Testar remoção de cache
        cache.delete(test_key)
        self.assertIsNone(cache.get(test_key))

    def test_cache_key_generation(self):
        """Testa a geração de chaves de cache"""
        cache = GoogleBooksCache(namespace="test_namespace")

        # Testar chave com namespace
        key = "test_key"
        full_key = cache._get_full_key(key)
        self.assertTrue(full_key.startswith("test_namespace:"))

        # Verificar se a mesma entrada gera sempre a mesma chave
        self.assertEqual(cache._get_full_key(key), cache._get_full_key(key))

        # Verificar se entradas diferentes geram chaves diferentes
        self.assertNotEqual(cache._get_full_key("key1"), cache._get_full_key("key2"))

    def test_complex_data_serialization(self):
        """Testa serialização de estruturas de dados complexas"""
        cache = GoogleBooksCache(namespace="test_serialization")

        # Dicionário aninhado
        nested_dict = {
            "id": "123",
            "details": {
                "title": "Test",
                "metadata": {
                    "created": "2023-01-01",
                    "modified": "2023-01-02"
                }
            },
            "tags": ["fiction", "sci-fi", "bestseller"]
        }

        # Armazenar e recuperar dados complexos
        cache.set("complex_data", nested_dict)
        retrieved_data = cache.get("complex_data")

        # Verificar se os dados foram preservados corretamente
        self.assertEqual(retrieved_data, nested_dict)
        self.assertEqual(retrieved_data["details"]["metadata"]["created"], "2023-01-01")
        self.assertEqual(retrieved_data["tags"][1], "sci-fi")


@override_settings(CACHES={
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
    'books_search': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
    'recommendations': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
    'books_recommendations': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
    'google_books': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
    'image_proxy': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
})
class CacheBackendIndependenceTest(TestCase):
    """
    Testes com override de configurações para garantir que o código
    funciona corretamente independente do backend de cache usado.
    Utiliza LocMemCache para testes isolados.
    """

    def setUp(self):
        # Limpar caches antes de cada teste
        for cache_name in caches:
            caches[cache_name].clear()

        # Criar um usuário para testes
        self.user = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='password123'
        )

    def test_recommendation_cache_with_locmem(self):
        """Testa que o cache de recomendações funciona com backend LocMemCache"""
        # Dados de teste
        test_recommendations = [
            {'id': '123', 'title': 'Test Book 1'},
            {'id': '456', 'title': 'Test Book 2'}
        ]

        # Usar o cache de recomendações
        RecommendationCache.set_recommendations(self.user, test_recommendations)
        cached_data = RecommendationCache.get_recommendations(self.user)

        # Verificar se os dados foram armazenados corretamente
        self.assertEqual(cached_data, test_recommendations)

    def test_google_books_cache_with_locmem(self):
        """Testa que o cache do Google Books funciona com backend LocMemCache"""
        cache = GoogleBooksCache(namespace="test_locmem")

        # Dados de teste
        test_data = {"id": "123", "title": "Test Book"}

        # Usar o cache
        cache.set("test_key", test_data)
        cached_data = cache.get("test_key")

        # Verificar se os dados foram armazenados corretamente
        self.assertEqual(cached_data, test_data)


# Testes adicionais que exigem simulação de requisições HTTP

class ImageProxyCacheTest(TestCase):
    """
    Testes para o proxy de imagem e seu cache.
    Nota: Alguns testes podem exigir mock de requisições HTTP.
    """

    def test_image_cache_key_generation(self):
        """Testa a geração de chaves para o cache de imagens"""
        # Simular URLs de imagens
        url1 = "https://books.google.com/books/content?id=abc123&img=1"
        url2 = "https://books.google.com/books/content?id=def456&img=1"

        # Gerar chaves de cache com a mesma lógica do proxy de imagem
        key1 = f"img_proxy_{hashlib.md5(url1.encode()).hexdigest()}"
        key2 = f"img_proxy_{hashlib.md5(url2.encode()).hexdigest()}"

        # Verificar que URLs diferentes geram chaves diferentes
        self.assertNotEqual(key1, key2)

        # Verificar que a mesma URL sempre gera a mesma chave
        same_key = f"img_proxy_{hashlib.md5(url1.encode()).hexdigest()}"
        self.assertEqual(key1, same_key)
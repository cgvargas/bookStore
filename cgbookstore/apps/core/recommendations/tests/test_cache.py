from django.test import TestCase
from django.core.cache import cache
from django.contrib.auth import get_user_model
from cgbookstore.apps.core.models import Book, UserBookShelf
from ..utils.cache_manager import RecommendationCache
from rest_framework.test import APIClient
from django.urls import reverse

User = get_user_model()


class RecommendationCacheTests(TestCase):
    def setUp(self):
        # Limpa o cache antes dos testes
        cache.clear()

        # Cria usuário de teste
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Cria livros de teste
        self.book1 = Book.objects.create(
            titulo='Livro 1',
            autor='Autor 1',
            categoria='Ficção'
        )

        self.book2 = Book.objects.create(
            titulo='Livro 2',
            autor='Autor 2',
            categoria='Ficção'
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_cache_recommendations(self):
        """Testa se as recomendações estão sendo cacheadas"""
        url = reverse('recommendations-api:recommendations')

        # Primeira requisição - deve gerar cache
        response1 = self.client.get(url)
        cached_data = RecommendationCache.get_recommendations(self.user)

        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response1.data, cached_data)

        # Segunda requisição - deve usar cache
        response2 = self.client.get(url)
        self.assertEqual(response1.data, response2.data)

    def test_cache_shelf(self):
        """Testa se a prateleira está sendo cacheada"""
        url = reverse('recommendations-api:personalized-shelf')

        # Primeira requisição - deve gerar cache
        response1 = self.client.get(url)
        cached_data = RecommendationCache.get_shelf(self.user)

        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response1.data, cached_data)

        # Segunda requisição - deve usar cache
        response2 = self.client.get(url)
        self.assertEqual(response1.data, response2.data)

    def test_cache_invalidation(self):
        """Testa se o cache é invalidado ao modificar prateleira"""
        # Gera cache inicial
        url = reverse('recommendations-api:recommendations')
        response1 = self.client.get(url)
        initial_cache = RecommendationCache.get_recommendations(self.user)

        # Adiciona livro à prateleira
        UserBookShelf.objects.create(
            user=self.user,
            book=self.book1,
            shelf_type='lido'
        )

        # Verifica se cache foi invalidado
        current_cache = RecommendationCache.get_recommendations(self.user)
        self.assertIsNone(current_cache)

        # Nova requisição deve gerar novo cache
        response2 = self.client.get(url)
        self.assertNotEqual(response1.data, response2.data)

    def tearDown(self):
        # Limpa o cache após os testes
        cache.clear()
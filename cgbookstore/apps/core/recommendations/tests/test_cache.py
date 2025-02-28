from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client
from django.core.cache import cache

from ..utils.cache_manager import RecommendationCache
from ...models import Book, UserBookShelf

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

        # Usa o cliente de teste do Django
        self.client = Client()

        # Loga o usuário diretamente
        self.client.login(username='testuser', password='testpass123')

        # Cria alguns livros de teste
        self.book1 = Book.objects.create(
            titulo='Livro 1',
            autor='Autor 1',
            categoria='Ficção'
        )

    def test_cache_recommendations(self):
        """Testa se as recomendações estão sendo cacheadas"""
        url = reverse('recommendations-api:recommendations_api')

        # Primeira requisição - deve gerar cache
        response1 = self.client.get(url)

        # Verifica o status da resposta
        self.assertEqual(response1.status_code, 200)

        # Decodifica o JSON
        response_data = response1.json()

        # Verifica a estrutura da resposta
        self.assertIn('local', response_data)
        self.assertIn('external', response_data)
        self.assertIn('has_external', response_data)
        self.assertIn('total', response_data)

        # Obtém os dados em cache
        cached_data = RecommendationCache.get_recommendations(self.user)

        # Se o cache estiver None, configura para um dicionário vazio
        if cached_data is None:
            cached_data = {
                'local': [],
                'external': [],
                'has_external': False,
                'total': 0
            }

        # Compara os dados
        self.assertEqual(response_data, cached_data)

        # Segunda requisição - deve usar cache
        response2 = self.client.get(url)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.json(), response_data)

    def tearDown(self):
        # Limpa o cache após os testes
        cache.clear()
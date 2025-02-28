from django.test import TestCase
from django.core.cache import cache, caches
from django.contrib.auth import get_user_model
from django.urls import reverse

from cgbookstore.apps.core.models import Book, UserBookShelf
from cgbookstore.apps.core.recommendations.engine import RecommendationEngine
import time
import random

User = get_user_model()


class RecommendationCacheTests(TestCase):
    def setUp(self):
        # Limpa todos os caches
        cache.clear()

        # Fixa a semente para consistência nos testes
        random.seed(42)

        # Cria usuário de teste
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        # Cria livros de teste
        self.books = []
        for i in range(20):  # Mais livros para aumentar variabilidade
            book = Book.objects.create(
                titulo=f'Livro {i}',
                autor=f'Autor {i}',
                categoria='Ficção'
            )
            self.books.append(book)

        # Adiciona alguns livros à prateleira
        UserBookShelf.objects.create(
            user=self.user,
            book=self.books[0],
            shelf_type='lido'
        )

        # Instancia o motor de recomendações
        self.engine = RecommendationEngine()

        User = get_user_model()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

    def test_recommendation_cache_creation(self):
        """Testa se as recomendações são cacheadas"""
        recommendation_cache = caches['recommendations']
        recommendation_cache.clear()

        # Primeira chamada - deve gerar recomendações
        first_recommendations = list(self.engine.get_recommendations(self.user))

        # Verifica se tem recomendações
        self.assertTrue(len(first_recommendations) > 0)

        # Segunda chamada deve usar cache
        second_recommendations = list(self.engine.get_recommendations(self.user))

        # Verifica se são iguais
        self.assertEqual(
            [r.id for r in first_recommendations],
            [r.id for r in second_recommendations],
            "Recomendações não foram cacheadas"
        )

    def test_recommendation_cache_invalidation(self):
        """Testa invalidação de cache ao modificar prateleira"""
        # Limpa cache
        recommendation_cache = caches['recommendations']
        recommendation_cache.clear()

        # Gera recomendações iniciais
        first_recommendations = list(self.engine.get_recommendations(self.user))
        first_ids = set(r.id for r in first_recommendations)

        # Adiciona novo livro à prateleira
        novo_livro = Book.objects.create(
            titulo='Novo Livro Único',
            autor='Novo Autor Especial',
            categoria='Ficção Experimental'
        )
        novo_shelf_item = UserBookShelf.objects.create(
            user=self.user,
            book=novo_livro,
            shelf_type='lido'
        )

        # Força invalidação manual do cache
        self.engine.invalidate_recommendations_cache(self.user)

        # Limpa qualquer cache residual
        recommendation_cache.clear()

        # Pequeno delay para garantir timestamp diferente
        import time
        time.sleep(1)

        # Nova chamada deve gerar novas recomendações
        new_recommendations = list(self.engine.get_recommendations(self.user))
        new_ids = set(r.id for r in new_recommendations)

        # Debug
        print("\nPrimeiras recomendações:", first_ids)
        print("Novas recomendações:", new_ids)

        # Verifica se as recomendações são diferentes
        self.assertTrue(
            len(first_ids.intersection(new_ids)) < len(first_ids),
            "Cache não foi invalidado após mudança na prateleira"
        )

    def test_recommendation_cache_timeout(self):
        """Testa timeout do cache de recomendações"""
        # Primeira chamada com timeout de 1 segundo
        first_recommendations = list(
            self.engine.get_recommendations(
                self.user,
                timeout=1  # 1 segundo de timeout
            )
        )

        # Espera para expirar
        import time
        time.sleep(2)  # Espera mais que o timeout

        # Segunda chamada
        second_recommendations = list(
            self.engine.get_recommendations(
                self.user,
                timeout=1  # 1 segundo de timeout
            )
        )

        # Imprime para debug
        print("\nPrimeiras recomendações:", [r.id for r in first_recommendations])
        print("Segundas recomendações:", [r.id for r in second_recommendations])

        # Verifica se as recomendações são diferentes
        self.assertTrue(
            len(set(r.id for r in first_recommendations).intersection(
                set(r.id for r in second_recommendations)
            )) < len(first_recommendations),
            "Cache não expirou corretamente"
        )

    def test_cache_recommendations(self):
        """Testa se as recomendações estão sendo cacheadas"""
        url = reverse('recommendations-api:recommendations_api')
        print(f"URL being tested: {url}")  # Debug

        response1 = self.client.get(url)
        print(f"Response status code: {response1.status_code}")  # Debug
        print(f"Response content: {response1.content}")  # Debug

        self.assertEqual(response1.status_code, 200)

        # Primeira requisição - deve gerar cache
        response1 = self.client.get(url)
        self.assertEqual(response1.status_code, 200)
        response_data = response1.json()

        # Verifica a estrutura da resposta
        self.assertIn('local', response_data)
        self.assertIn('external', response_data)
        self.assertIn('has_external', response_data)
        self.assertIn('total', response_data)

        # Obtém os dados em cache
        cache_key = self.engine._get_cache_key(self.user)
        cached_data = self.engine._cache.get(cache_key)

        # Compara os dados
        self.assertEqual(response_data, cached_data)

    def tearDown(self):
        # Limpa o cache no final dos testes
        cache.clear()
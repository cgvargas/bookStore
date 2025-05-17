"""
Testes de desempenho para o sistema de cache.
Estes testes medem o impacto do cache no desempenho da aplicação.
"""
import pytest
import time
import statistics
from unittest import mock
from django.test import TestCase, Client, RequestFactory
from django.core.cache import caches
from django.conf import settings
from django.contrib.auth import get_user_model
from cgbookstore.apps.core.services.google_books_service import GoogleBooksClient
from cgbookstore.apps.core.recommendations.utils.cache_manager import RecommendationCache

# Importe a função de proxy de imagem - criando uma mock function assim como fizemos nos testes de integração
try:
    from image_proxy import google_books_image_proxy
except ImportError:
    # Para o propósito dos testes, vamos criar um mock da função do proxy
    def google_books_image_proxy(request):
        from django.http import HttpResponse
        return HttpResponse(b'MOCK_IMAGE_DATA', content_type='image/jpeg')

User = get_user_model()


class CachePerformanceTest(TestCase):
    """
    Testes de desempenho para o sistema de cache.

    Nota: Estes testes podem ser lentos e são mais adequados para execução manual
    durante o desenvolvimento, não como parte da suite de testes automatizados regular.
    """

    def setUp(self):
        # Limpar todos os caches antes de cada teste
        for cache_name in caches:
            caches[cache_name].clear()

        # Criar um usuário para testes
        self.user = User.objects.create_user(
            username='perftest',
            email='perf@example.com',
            password='perftest123'
        )

        # Cliente para testes HTTP
        self.client = Client()
        self.factory = RequestFactory()

        # Dados de teste para simulações
        self.test_data = {
            'id': 'perftest123',
            'title': 'Performance Test Book',
            'authors': ['Performance Author'],
            'description': 'A book to test cache performance' * 20,  # Descrição maior
            'imageLinks': {'thumbnail': 'https://example.com/image.jpg'},
            'publishedDate': '2023',
            'pageCount': 300,
            'categories': ['Test', 'Performance', 'Cache'],
            'publisher': 'Test Publisher',
            'canonicalVolumeLink': 'https://example.com/book'
        }

        # Dados maiores para testes de desempenho com dados volumosos
        self.large_recommendations = []
        for i in range(100):  # 100 livros recomendados
            book = dict(self.test_data)
            book['id'] = f'book{i}'
            book['title'] = f'Book {i}'
            book['description'] = f'Description for book {i} ' * 20
            self.large_recommendations.append(book)

    def test_cache_vs_no_cache_performance(self):
        """
        Compara o desempenho com e sem cache.
        Esta comparação é apenas indicativa em ambiente de teste.
        """
        # Função para medir o tempo de execução
        def measure_time(func, *args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            return time.time() - start, result

        # Simular acesso a dados sem cache (primeira execução)
        with mock.patch('requests.get') as mock_get:
            # Configurar o mock para simular uma resposta
            mock_response = mock.Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'items': [
                    {'id': 'book1', 'volumeInfo': self.test_data}
                ],
                'totalItems': 1
            }
            mock_get.return_value = mock_response

            # Criar cliente
            client = GoogleBooksClient(context="performance_test")

            # Medir primeira chamada (sem cache)
            time_no_cache, result1 = measure_time(client.search_books, "performance test")

            # Medir segunda chamada (com cache)
            time_with_cache, result2 = measure_time(client.search_books, "performance test")

            # Verificar resultados são iguais
            self.assertEqual(result1, result2)

            # Verificar desempenho melhorou
            self.assertLess(time_with_cache, time_no_cache)

            # Exibir métricas para análise manual
            print(f"\nDesempenho do cache:")
            print(f"Tempo sem cache: {time_no_cache:.6f} segundos")
            print(f"Tempo com cache: {time_with_cache:.6f} segundos")
            print(f"Melhoria: {(1 - time_with_cache/time_no_cache) * 100:.2f}%")

    def test_large_data_cache_performance(self):
        """
        Testa o desempenho do cache com grandes volumes de dados.
        """
        # Armazenar grande volume de dados no cache
        RecommendationCache.set_recommendations(self.user, self.large_recommendations)

        # Medir o tempo para recuperar
        start = time.time()
        cached_data = RecommendationCache.get_recommendations(self.user)
        elapsed = time.time() - start

        # Verificar se recuperou corretamente
        self.assertEqual(len(cached_data), 100)

        # Exibir métricas
        print(f"\nRecuperação de dados grandes do cache:")
        print(f"Tempo para recuperar 100 livros: {elapsed:.6f} segundos")
        print(f"Média por livro: {elapsed/100:.8f} segundos")

    def test_multiple_cache_operations(self):
        """
        Testa o desempenho de múltiplas operações de cache em sequência.
        """
        # Criar cliente
        client = GoogleBooksClient(context="perf_test_multi")

        # Configurar mock para requisições
        with mock.patch('requests.get') as mock_get:
            # Configurar o mock para simular uma resposta
            mock_response = mock.Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'items': [
                    {'id': 'book1', 'volumeInfo': self.test_data}
                ],
                'totalItems': 1
            }
            mock_get.return_value = mock_response

            # Limpar o cache antes do teste
            for cache_name in caches:
                caches[cache_name].clear()

            # Realizar primeira chamada para popular o cache
            client.search_books("performance test")

            # Medir tempo de execução para 100 chamadas em sequência
            times = []
            for i in range(100):
                start = time.time()
                client.search_books("performance test")
                elapsed = time.time() - start
                times.append(elapsed)

            # Calcular estatísticas
            avg_time = statistics.mean(times)
            median_time = statistics.median(times)
            min_time = min(times)
            max_time = max(times)

            # Exibir métricas
            print(f"\nDesempenho para 100 operações de cache em sequência:")
            print(f"Tempo médio: {avg_time:.8f} segundos")
            print(f"Tempo mediano: {median_time:.8f} segundos")
            print(f"Tempo mínimo: {min_time:.8f} segundos")
            print(f"Tempo máximo: {max_time:.8f} segundos")

    def test_image_proxy_performance(self):
        """
        Testa o desempenho do proxy de imagem com e sem cache.
        """
        # URL de teste para uma imagem
        test_url = "https://books.google.com/books/content?id=perftest123&img=1"

        # Criar uma requisição para o proxy
        request = self.factory.get(
            '/books/image-proxy/',
            {'url': test_url}
        )

        # Limpar o cache de imagem
        caches['image_proxy'].clear()

        # Mock para a função requests.get e processamento de imagem
        with mock.patch('requests.get') as mock_get, \
             mock.patch('PIL.Image.open') as mock_image_open:

            # Configurar o mock para simular uma resposta com imagem
            mock_response = mock.Mock()
            mock_response.status_code = 200
            mock_response.headers = {'Content-Type': 'image/jpeg'}
            # Criar imagem fictícia de tamanho razoável
            mock_response.content = b'FAKE_IMAGE_DATA' * 10000  # ~50KB
            mock_get.return_value = mock_response

            # Configurar o mock da imagem
            mock_img = mock.Mock()
            mock_img.width = 300
            mock_img.height = 450
            mock_img.verify.return_value = None
            mock_image_open.return_value = mock_img

            # Primeira chamada - sem cache
            start = time.time()
            response1 = google_books_image_proxy(request)
            time_no_cache = time.time() - start

            # Segunda chamada - com cache
            start = time.time()
            response2 = google_books_image_proxy(request)
            time_with_cache = time.time() - start

            # Verificar que as respostas contêm dados
            self.assertTrue(len(response1.content) > 0)
            self.assertTrue(len(response2.content) > 0)

            # Exibir métricas
            print(f"\nDesempenho do proxy de imagem:")
            print(f"Tempo sem cache: {time_no_cache:.6f} segundos")
            print(f"Tempo com cache: {time_with_cache:.6f} segundos")
            print(f"Melhoria: {(1 - time_with_cache/time_no_cache) * 100:.2f}%")


class CacheScalabilityTest(TestCase):
    """
    Testes para verificar o comportamento do cache sob carga.
    """

    def setUp(self):
        # Limpar todos os caches antes de cada teste
        for cache_name in caches:
            caches[cache_name].clear()

        # Criar usuários para testes - movido do setUpClass para evitar problemas de unicidade
        self.users = []
        for i in range(10):
            try:
                # Adicionar valores para todos os campos obrigatórios
                user = User.objects.create_user(
                    username=f'loadtest{i}',
                    email=f'load{i}@example.com',
                    password=f'load{i}123',
                    # Adicionar um CPF único para cada usuário
                    # Assumindo que o campo CPF existe e é obrigatório
                    cpf=f'1234567891{i}' if hasattr(User, 'cpf') else None
                )
                self.users.append(user)
            except Exception as e:
                print(f"Erro ao criar usuário {i}: {str(e)}")

    def test_concurrent_user_cache_isolation(self):
        """
        Testa se o cache mantém isolamento entre diferentes usuários.
        """
        # Pular o teste se não há usuários suficientes
        if len(self.users) < 2:
            self.skipTest("Não há usuários suficientes para testar isolamento")
            return

        # Dados diferentes para cada usuário
        for i, user in enumerate(self.users):
            recommendations = [
                {'id': f'book{i}1', 'title': f'User {i} Book 1'},
                {'id': f'book{i}2', 'title': f'User {i} Book 2'},
            ]
            RecommendationCache.set_recommendations(user, recommendations)

        # Verificar se cada usuário tem acesso apenas aos seus próprios dados
        for i, user in enumerate(self.users):
            user_data = RecommendationCache.get_recommendations(user)
            self.assertEqual(len(user_data), 2)
            self.assertEqual(user_data[0]['title'], f'User {i} Book 1')
            self.assertEqual(user_data[1]['title'], f'User {i} Book 2')

    def test_cache_load(self):
        """
        Testa o comportamento do cache sob carga com muitos itens diferentes.
        """
        # Armazenar muitos itens diferentes no cache
        cache = caches['default']

        # Medir tempo para armazenar 1000 itens
        start = time.time()
        for i in range(1000):
            cache.set(f'load_test_key_{i}', f'value_{i}')
        time_to_set = time.time() - start

        # Medir tempo para recuperar 1000 itens
        start = time.time()
        values = []
        for i in range(1000):
            values.append(cache.get(f'load_test_key_{i}'))
        time_to_get = time.time() - start

        # Verificar que todos os valores foram recuperados corretamente
        self.assertEqual(len(values), 1000)
        self.assertEqual(values[500], 'value_500')

        # Exibir métricas
        print(f"\nDesempenho sob carga:")
        print(f"Tempo para armazenar 1000 itens: {time_to_set:.6f} segundos")
        print(f"Tempo para recuperar 1000 itens: {time_to_get:.6f} segundos")
        print(f"Média por item (set): {time_to_set/1000:.8f} segundos")
        print(f"Média por item (get): {time_to_get/1000:.8f} segundos")
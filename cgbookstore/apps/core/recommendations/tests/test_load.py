import time
from concurrent.futures import ThreadPoolExecutor
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from cgbookstore.apps.core.models import Book, UserBookShelf
from django.test.utils import override_settings

User = get_user_model()


@override_settings(SESSION_ENGINE='django.contrib.sessions.backends.cache')
class RecommendationLoadTests(TestCase):
    """Testes de carga para o sistema de recomendações"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

        # Criar dados de teste
        self.setup_test_data()

    def setup_test_data(self):
        """Configura dados para teste de carga"""
        # Criar livros
        self.books = []
        for i in range(100):
            book = Book.objects.create(
                titulo=f'Livro {i}',
                autor=f'Autor {i % 10}',
                genero=f'Genero {i % 5}'
            )
            self.books.append(book)

        # Criar histórico de leitura
        for i in range(20):
            UserBookShelf.objects.create(
                user=self.user,
                book=self.books[i],
                shelf_type='lido'
            )

    def simulate_user_request(self):
        """Simula uma requisição de usuário"""
        url = reverse('recommendations:recommendations')
        response = self.client.get(url)
        return response

    def test_concurrent_users(self):
        """Testa performance com múltiplos usuários simultâneos"""
        NUM_USERS = 10  # Reduzido para teste inicial

        def make_request():
            start = time.time()
            response = self.simulate_user_request()
            end = time.time()
            return end - start

        with ThreadPoolExecutor(max_workers=5) as executor:
            response_times = list(executor.map(lambda _: make_request(), range(NUM_USERS)))

        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)

        print(f"\nTeste de Carga Resultados:")
        print(f"Usuários Simultâneos: {NUM_USERS}")
        print(f"Tempo Médio: {avg_time:.2f}s")
        print(f"Tempo Máximo: {max_time:.2f}s")
        print(f"Tempo Mínimo: {min_time:.2f}s")
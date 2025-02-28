from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
from ...models import Book, UserBookShelf
from ..providers.history import HistoryBasedProvider
from ..providers.temporal import TemporalProvider

User = get_user_model()


class TestHistoryTemporalProviders(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            cpf='12345678901'
        )

        # Cria alguns livros com características diferentes
        self.books = []
        genres = ['Fantasia', 'Ficção', 'Romance']
        categories = ['Juvenil', 'Adulto', 'Infantil']

        for i in range(10):
            book = Book.objects.create(
                titulo=f'Livro {i}',
                genero=genres[i % 3],
                categoria=categories[i % 3],
                autor=f'Autor {i % 2}'
            )
            self.books.append(book)

        # Cria histórico de leitura com datas diferentes
        dates = [
            timezone.now() - timedelta(days=10),
            timezone.now() - timedelta(days=40),
            timezone.now() - timedelta(days=70),
        ]

        shelf_types = ['lido', 'lendo', 'favorito']

        for i, book in enumerate(self.books[:6]):
            UserBookShelf.objects.create(
                user=self.user,
                book=book,
                shelf_type=shelf_types[i % 3],
                added_at=dates[i % 3]
            )

        self.history_provider = HistoryBasedProvider()
        self.temporal_provider = TemporalProvider()

    def test_history_recommendations(self):
        """Testa se o HistoryProvider retorna recomendações válidas"""
        recommendations = self.history_provider.get_recommendations(self.user)

        self.assertTrue(recommendations.exists())
        self.assertLessEqual(recommendations.count(), 20)

        # Verifica se não há livros da estante nas recomendações
        shelf_books = set(UserBookShelf.objects.filter(
            user=self.user
        ).values_list('book_id', flat=True))

        rec_books = set(recommendations.values_list('id', flat=True))
        self.assertFalse(shelf_books & rec_books)

    def test_temporal_recommendations(self):
        """Testa se o TemporalProvider retorna recomendações válidas"""
        recommendations = self.temporal_provider.get_recommendations(self.user)

        self.assertTrue(recommendations.exists())
        self.assertLessEqual(recommendations.count(), 20)

        # Verifica exclusões
        shelf_books = set(UserBookShelf.objects.filter(
            user=self.user
        ).values_list('book_id', flat=True))

        rec_books = set(recommendations.values_list('id', flat=True))
        self.assertFalse(shelf_books & rec_books)

    def test_seasonal_patterns(self):
        """Testa se os padrões sazonais estão sendo calculados corretamente"""
        patterns = self.temporal_provider.get_temporal_patterns(self.user)

        self.assertIn('seasonal', patterns)
        self.assertIn('rolling', patterns)

        current_season = self.temporal_provider.seasonal_analyzer.get_current_season()
        self.assertIn(current_season, patterns['seasonal'])

    def test_reading_patterns(self):
        """Testa se os padrões de leitura estão sendo calculados corretamente"""
        patterns = self.history_provider.get_reading_patterns(self.user)

        self.assertIn('genres', patterns)
        self.assertIn('authors', patterns)
        self.assertIn('categories', patterns)

        # Verifica se os padrões refletem os dados de teste
        self.assertTrue(len(patterns['genres']) > 0)
        self.assertTrue(len(patterns['authors']) > 0)
        self.assertTrue(len(patterns['categories']) > 0)

    def test_empty_history(self):
        """Testa comportamento com usuário sem histórico"""
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='newpass123',
            cpf='98765432109'
        )

        history_recs = self.history_provider.get_recommendations(new_user)
        temporal_recs = self.temporal_provider.get_recommendations(new_user)

        self.assertFalse(history_recs.exists())
        self.assertFalse(temporal_recs.exists())
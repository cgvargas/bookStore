from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import date
from ...models import Book, UserBookShelf
from ..providers.history import HistoryBasedProvider
from ..providers.category import CategoryBasedProvider
from ..providers.similarity import SimilarityBasedProvider

User = get_user_model()


class ProvidersTestCase(TestCase):
    def setUp(self):
        # Cria usuário de teste
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            cpf='12345678901'
        )

        # Cria conjunto de livros para teste
        self.fantasy_books = []
        self.science_books = []

        # Cria livros de fantasia
        for i in range(3):
            book = Book.objects.create(
                titulo=f'Fantasy Book {i}',
                autor='Fantasy Author',
                genero='Fiction',
                categoria='Fantasy',
                data_publicacao=date(2020 + i, 1, 1),
                temas='magic, adventure, fantasy'
            )
            self.fantasy_books.append(book)

        # Cria livros de ciência
        for i in range(3):
            book = Book.objects.create(
                titulo=f'Science Book {i}',
                autor='Science Author',
                genero='Non-Fiction',
                categoria='Science',
                data_publicacao=date(2020 + i, 1, 1),
                temas='physics, space, science'
            )
            self.science_books.append(book)

        # Adiciona alguns livros à prateleira do usuário
        UserBookShelf.objects.create(
            user=self.user,
            book=self.fantasy_books[0],
            shelf_type='lido'
        )
        UserBookShelf.objects.create(
            user=self.user,
            book=self.science_books[0],
            shelf_type='lido'
        )
        UserBookShelf.objects.create(
            user=self.user,
            book=self.fantasy_books[1],
            shelf_type='favorito'
        )


class HistoryProviderTests(ProvidersTestCase):
    def setUp(self):
        super().setUp()
        self.provider = HistoryBasedProvider()

    def test_get_recommendations(self):
        """Testa recomendações baseadas em histórico"""
        recommendations = self.provider.get_recommendations(self.user)
        self.assertTrue(len(recommendations) > 0)

    def test_reading_patterns(self):
        """Testa análise de padrões de leitura"""
        patterns = self.provider.get_reading_patterns(self.user)

        self.assertEqual(patterns['total_books'], 2)
        self.assertIn('Fantasy Author', patterns['favorite_authors'])
        self.assertIn('Fiction', patterns['favorite_genres'])


class CategoryProviderTests(ProvidersTestCase):
    def setUp(self):
        super().setUp()
        self.provider = CategoryBasedProvider()

    def test_get_recommendations(self):
        """Testa recomendações baseadas em categoria"""
        recommendations = self.provider.get_recommendations(self.user)
        self.assertTrue(len(recommendations) > 0)

    def test_category_affinity(self):
        """Testa cálculo de afinidade com categorias"""
        affinity = self.provider.get_category_affinity(self.user)

        self.assertIn('Fiction', affinity['genres'])
        self.assertIn('Fantasy', affinity['categories'])
        self.assertIn('magic', affinity['themes'])


class SimilarityProviderTests(ProvidersTestCase):
    def setUp(self):
        super().setUp()
        self.provider = SimilarityBasedProvider()

    def test_get_recommendations(self):
        """Testa recomendações baseadas em similaridade"""
        recommendations = self.provider.get_recommendations(self.user)
        self.assertTrue(len(recommendations) > 0)

    def test_similarity_score(self):
        """Testa cálculo de score de similaridade"""
        score = self.provider.calculate_similarity_score(
            self.fantasy_books[0],
            self.fantasy_books[1]
        )
        self.assertGreater(score, 0.5)  # Livros similares devem ter score alto

        score = self.provider.calculate_similarity_score(
            self.fantasy_books[0],
            self.science_books[0]
        )
        self.assertLess(score, 0.5)  # Livros diferentes devem ter score baixo
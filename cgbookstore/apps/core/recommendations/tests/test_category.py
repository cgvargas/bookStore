from django.test import TestCase
from django.contrib.auth import get_user_model
from ...models import Book, UserBookShelf
from ..providers.category import CategoryBasedProvider
from unittest.mock import patch

User = get_user_model()


class CategoryBasedProviderTest(TestCase):
    def setUp(self):
        # Criar usuário de teste
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Criar livros de teste com diferentes categorias
        self.book_python = Book.objects.create(
            titulo='Python Programming',
            categoria="['Computers']",
            quantidade_vendida=10,
            quantidade_acessos=100
        )

        self.book_fantasy = Book.objects.create(
            titulo='Epic Fantasy',
            categoria='Fiction',
            genero='Fantasia Épica',
            quantidade_vendida=20,
            quantidade_acessos=200
        )

        self.book_religion = Book.objects.create(
            titulo='Religious Book',
            categoria="['Religion']",
            quantidade_vendida=5,
            quantidade_acessos=50
        )

        # Criar prateleiras de teste
        UserBookShelf.objects.create(
            user=self.user,
            book=self.book_python,
            shelf_type='favorito'
        )

        self.provider = CategoryBasedProvider()

    def test_analyze_user_preferences(self):
        """Testa se as preferências do usuário são corretamente analisadas"""
        preferences = self.provider._analyze_user_preferences(self.user)

        self.assertIn('programming', preferences['categories'])
        self.assertGreater(preferences['categories']['programming'], 0)

    def test_get_recommendations_exclude_shelf_books(self):
        """Testa se livros na prateleira são excluídos das recomendações"""
        recommendations = self.provider.get_recommendations(self.user)

        # Verifica se o livro da prateleira não está nas recomendações
        self.assertNotIn(self.book_python, recommendations)

    def test_recommendations_ordering(self):
        """Testa se as recomendações são ordenadas corretamente"""
        # Criar mais livros com métricas diferentes
        book_high_metrics = Book.objects.create(
            titulo='Popular Book',
            categoria="['Computers']",
            quantidade_vendida=100,
            quantidade_acessos=1000
        )

        book_low_metrics = Book.objects.create(
            titulo='Less Popular Book',
            categoria="['Computers']",
            quantidade_vendida=1,
            quantidade_acessos=10
        )

        recommendations = self.provider.get_recommendations(self.user)

        # Verifica se o livro com métricas mais altas aparece primeiro
        high_index = -1
        low_index = -1

        for i, book in enumerate(recommendations):
            if book.id == book_high_metrics.id:
                high_index = i
            if book.id == book_low_metrics.id:
                low_index = i

        if high_index != -1 and low_index != -1:
            self.assertLess(high_index, low_index)

    def test_get_recommendations_limit(self):
        """Testa se o limite de recomendações é respeitado"""
        limit = 5
        recommendations = self.provider.get_recommendations(self.user, limit=limit)
        self.assertLessEqual(len(recommendations), limit)

    def test_category_affinity(self):
        """Testa o cálculo de afinidade por categoria"""
        affinity = self.provider.get_category_affinity(self.user)

        self.assertIn('categories', affinity)
        self.assertIn('genres', affinity)
        self.assertIn('themes', affinity)

        # Verifica se a categoria do livro favorito tem peso maior
        if 'programming' in affinity['categories']:
            self.assertGreaterEqual(
                affinity['categories']['programming'],
                CategoryBasedProvider.SHELF_WEIGHTS['favorito']
            )

    def test_fallback_recommendations(self):
        """Testa se as recomendações fallback são geradas quando necessário"""
        # Remove todos os livros similares
        Book.objects.all().delete()

        # Cria alguns livros populares para fallback
        popular_book = Book.objects.create(
            titulo='Popular Book',
            quantidade_vendida=100,
            quantidade_acessos=1000,
            e_destaque=True
        )

        recommendations = self.provider.get_recommendations(self.user)
        self.assertGreater(len(recommendations), 0)
        self.assertIn(popular_book, recommendations)

    def test_secondary_recommendations(self):
        """Testa se as recomendações secundárias são geradas corretamente"""
        book_related = Book.objects.create(
            titulo='Related Book',
            categoria='Programming',
            temas='python, programming'
        )

        preferences = self.provider._analyze_user_preferences(self.user)
        excluded_books = {self.book_python.id}

        secondary_recs = self.provider._get_secondary_recommendations(
            preferences,
            excluded_books
        )

        self.assertIn(book_related, secondary_recs)
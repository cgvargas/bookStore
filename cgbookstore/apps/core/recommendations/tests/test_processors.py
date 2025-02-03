from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import date
from ...models import Book, UserBookShelf
from ..utils.processors import CategoryProcessor, SimilarityProcessor

User = get_user_model()


class ProcessorsTestCase(TestCase):
    def setUp(self):
        # Cria usuário de teste
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            cpf='12345678901'
        )

        # Cria livros para teste
        self.books = []

        # Livros de fantasia
        for i in range(3):
            book = Book.objects.create(
                titulo=f'Fantasy {i}',
                autor='Author 1',
                genero='Fiction',
                categoria='Fantasy',
                data_publicacao=date(2020 + i, 1, 1),
                temas='magic, adventure, fantasy'
            )
            self.books.append(book)
            UserBookShelf.objects.create(
                user=self.user,
                book=book,
                shelf_type='lido'
            )

        # Livros de ficção científica
        for i in range(2):
            book = Book.objects.create(
                titulo=f'SciFi {i}',
                autor='Author 2',
                genero='Fiction',
                categoria='Science Fiction',
                data_publicacao=date(2020 + i, 1, 1),
                temas='space, future, technology'
            )
            self.books.append(book)
            UserBookShelf.objects.create(
                user=self.user,
                book=book,
                shelf_type='lido'
            )


class CategoryProcessorTests(ProcessorsTestCase):
    def setUp(self):
        super().setUp()
        self.processor = CategoryProcessor()

    def test_extract_preferences(self):
        """Testa extração de preferências do usuário"""
        read_books = UserBookShelf.objects.filter(
            user=self.user,
            shelf_type='lido'
        )

        preferences = self.processor.extract_preferences(read_books)

        # Verifica gêneros
        self.assertIn('Fiction', preferences['genres'])

        # Verifica categorias
        self.assertIn('Fantasy', preferences['categories'])
        self.assertIn('Science Fiction', preferences['categories'])

        # Verifica temas
        self.assertTrue(any('magic' in t for t in preferences['themes']))
        self.assertTrue(any('space' in t for t in preferences['themes']))

    def test_most_common_calculation(self):
        """Testa cálculo de items mais comuns"""
        items = ['a', 'a', 'b', 'b', 'b', 'c']
        result = self.processor._get_most_common(items, 2)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], 'b')  # Mais comum
        self.assertEqual(result[1], 'a')  # Segundo mais comum


class SimilarityProcessorTests(ProcessorsTestCase):
    def setUp(self):
        super().setUp()
        self.processor = SimilarityProcessor()

    def test_calculate_similarity_same_genre(self):
        """Testa similaridade entre livros do mesmo gênero"""
        score = self.processor.calculate_similarity(self.books[0], self.books[1])
        self.assertGreater(score, 0.7)  # Score deve ser alto para livros similares

    def test_calculate_similarity_different_genre(self):
        """Testa similaridade entre livros de gêneros diferentes"""
        score = self.processor.calculate_similarity(self.books[0], self.books[3])
        self.assertLess(score, 0.5)  # Score deve ser baixo para livros diferentes

    def test_calculate_similarity_same_author(self):
        """Testa similaridade entre livros do mesmo autor"""
        book1 = self.books[0]  # Author 1
        book2 = self.books[1]  # Author 1
        score = self.processor.calculate_similarity(book1, book2)
        self.assertGreater(score, 0.3)  # Deve considerar autor igual

    def test_calculate_similarity_different_author(self):
        """Testa similaridade entre livros de autores diferentes"""
        book1 = self.books[0]  # Author 1
        book2 = self.books[3]  # Author 2
        score = self.processor.calculate_similarity(book1, book2)
        self.assertLess(score, 0.7)  # Deve considerar autor diferente
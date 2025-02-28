from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import date
from ...models import Book, UserBookShelf
from ..engine import RecommendationEngine

User = get_user_model()


class RecommendationEngineTests(TestCase):
    def setUp(self):
        # Cria usuário de teste
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            cpf='12345678901'
        )

        # Cria alguns livros de teste
        self.book1 = Book.objects.create(
            titulo='Book 1',
            autor='Author 1',
            genero='Fiction',
            categoria='Fantasy',
            data_publicacao=date(2020, 1, 1),
            temas='magic, adventure'
        )

        self.book2 = Book.objects.create(
            titulo='Book 2',
            autor='Author 1',
            genero='Fiction',
            categoria='Fantasy',
            data_publicacao=date(2021, 1, 1),
            temas='magic, dragons'
        )

        self.book3 = Book.objects.create(
            titulo='Book 3',
            autor='Author 2',
            genero='Non-Fiction',
            categoria='Science',
            data_publicacao=date(2022, 1, 1),
            temas='physics, space'
        )

        # Cria prateleira de livros do usuário
        UserBookShelf.objects.create(
            user=self.user,
            book=self.book1,
            shelf_type='lido'
        )

        # Cria mais alguns livros de teste
        for i in range(10):
            Book.objects.create(
                titulo=f'Extra Book {i}',
                autor=f'Extra Author {i}',
                genero='Mixed',
                categoria='General',
                data_publicacao=date(2023, 1, 1),
                temas='general, mixed'
            )

        self.engine = RecommendationEngine()

    def test_get_recommendations(self):
        """Testa se o engine retorna recomendações válidas"""
        recommendations = self.engine.get_recommendations(self.user)

        self.assertTrue(len(recommendations) > 0)
        self.assertNotIn(self.book1, recommendations)  # Não deve recomendar livro já lido

    def test_get_personalized_shelf(self):
        """Testa se o engine cria prateleira personalizada"""
        shelf = self.engine.get_personalized_shelf(self.user)

        self.assertIn('based_on_history', shelf)
        self.assertIn('based_on_categories', shelf)
        self.assertIn('you_might_like', shelf)

    def test_recommendations_limit(self):
        """Testa se o limite de recomendações é respeitado"""
        limit = 5
        recommendations = self.engine.get_recommendations(self.user, limit=limit)

        self.assertLessEqual(len(recommendations), limit)

    def test_new_user_recommendations(self):
        """Testa recomendações para usuário novo sem histórico"""
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='newpass123',
            cpf='98765432101'
        )

        recommendations = self.engine.get_recommendations(new_user)
        self.assertTrue(len(recommendations) > 0)  # Deve retornar algo mesmo sem histórico
        self.assertLessEqual(len(recommendations), self.engine.DEFAULT_LIMIT)  # Não deve exceder o limite padrão

        # Verifica se as recomendações são instâncias de Book
        for book in recommendations:
            self.assertIsInstance(book, Book)
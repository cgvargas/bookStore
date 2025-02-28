from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from cgbookstore.apps.core.models import Book, UserBookShelf

User = get_user_model()


class RecommendationsAPITests(TestCase):
    def setUp(self):
        # Criar usuário de teste
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Criar alguns livros de teste
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

        # Criar entrada na prateleira
        UserBookShelf.objects.create(
            user=self.user,
            book=self.book1,
            shelf_type='lido'
        )

        # Cliente API
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_get_recommendations(self):
        """Testa o endpoint de recomendações gerais"""
        url = reverse('recommendations:recommendations')  # Alterado o namespace
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.data, list))

        # Verifica se o livro já lido não está nas recomendações
        book_ids = [book['id'] for book in response.data]
        self.assertNotIn(self.book1.id, book_ids)

    def test_get_personalized_shelf(self):
        """Testa o endpoint de prateleira personalizada"""
        url = reverse('recommendations:personalized-shelf')  # Alterado o namespace
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn('based_on_history', response.data)
        self.assertIn('based_on_categories', response.data)
        self.assertIn('you_might_like', response.data)
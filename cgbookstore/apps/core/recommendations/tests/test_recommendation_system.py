from django.test import TestCase
from django.contrib.auth import get_user_model
from ...models import Book, UserBookShelf
from ..engine import RecommendationEngine
from ..providers.history import HistoryBasedProvider
from ..providers.similarity import SimilarityBasedProvider

User = get_user_model()

class RecommendationSystemTest(TestCase):
    def setUp(self):
        # Criar usuários de teste com CPF
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='password123',
            cpf='12345678901'  # CPF de teste para user1
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@test.com',
            password='password123',
            cpf='12345678902'  # CPF de teste para user2
        )

        # Criar livros de teste - Usuário 1 (Preferência: Ficção Científica)
        self.sci_fi_books = []
        for i in range(5):
            book = Book.objects.create(
                titulo=f'Sci-Fi Book {i}',
                autor='Arthur C. Clarke',
                genero='Ficção Científica',
                categoria='Ficção',
                temas='espaço,tecnologia,futuro'
            )
            self.sci_fi_books.append(book)
            if i < 3:  # Adicionar 3 livros à estante do user1
                UserBookShelf.objects.create(
                    user=self.user1,
                    book=book,
                    shelf_type='lido'
                )

        # Criar livros de teste - Usuário 2 (Preferência: Romance)
        self.romance_books = []
        for i in range(5):
            book = Book.objects.create(
                titulo=f'Romance Book {i}',
                autor='Jane Austen',
                genero='Romance',
                categoria='Ficção',
                temas='amor,relacionamento,sociedade'
            )
            self.romance_books.append(book)
            if i < 3:  # Adicionar 3 livros à estante do user2
                UserBookShelf.objects.create(
                    user=self.user2,
                    book=book,
                    shelf_type='lido'
                )

    def test_recommendations_personalization(self):
        """Testa se as recomendações são personalizadas por usuário"""
        engine = RecommendationEngine()

        # Obter recomendações para user1
        recommendations_user1 = engine.get_recommendations(self.user1)

        # Obter recomendações para user2
        recommendations_user2 = engine.get_recommendations(self.user2)

        # Verificar se as recomendações são diferentes
        self.assertNotEqual(
            set(recommendations_user1.values_list('id', flat=True)),
            set(recommendations_user2.values_list('id', flat=True)),
            "As recomendações devem ser diferentes para usuários diferentes"
        )

    def test_exclusion_of_read_books(self):
        """Testa se livros já lidos são excluídos das recomendações"""
        engine = RecommendationEngine()

        # Obter recomendações para user1
        recommendations = engine.get_recommendations(self.user1)

        # Obter IDs dos livros já lidos
        read_books = UserBookShelf.objects.filter(
            user=self.user1,
            shelf_type='lido'
        ).values_list('book_id', flat=True)

        # Verificar se nenhum livro lido está nas recomendações
        recommended_ids = recommendations.values_list('id', flat=True)
        for book_id in read_books:
            self.assertNotIn(
                book_id,
                recommended_ids,
                "Livros já lidos não devem aparecer nas recomendações"
            )

    def test_similarity_provider(self):
        """Testa se o provider de similaridade está funcionando corretamente"""
        provider = SimilarityBasedProvider()

        # Testar similaridade entre livros do mesmo gênero
        similarity_score = provider.calculate_similarity_score(
            self.sci_fi_books[0],
            self.sci_fi_books[1]
        )
        self.assertGreater(
            similarity_score,
            0.5,
            "Livros do mesmo gênero devem ter alta similaridade"
        )

    def test_history_based_recommendations(self):
        """Testa se as recomendações baseadas em histórico estão corretas"""
        provider = HistoryBasedProvider()

        # Obter recomendações baseadas em histórico para user1
        recommendations = provider.get_recommendations(self.user1)

        # Verificar se as recomendações seguem o padrão de leitura
        if recommendations.exists():
            book = recommendations.first()
            self.assertTrue(
                book.genero == 'Ficção Científica' or book.autor == 'Arthur C. Clarke',
                "As recomendações devem seguir o gênero ou autor preferido do usuário"
            )

    def test_cache_invalidation(self):
        """Testa se as recomendações mudam após alterações na estante"""
        engine = RecommendationEngine()

        # Adicionar mais livros para garantir recomendações diferentes
        for i in range(3):
            Book.objects.create(
                titulo=f'Extra Sci-Fi Book {i}',
                autor='Isaac Asimov',
                genero='Ficção Científica',
                categoria='Ficção',
                temas='robôs,tecnologia,futuro'
            )

        # Obter recomendações iniciais
        initial_recommendations = engine.get_recommendations(self.user1, limit=3)
        initial_ids = set(initial_recommendations.values_list('id', flat=True))

        # Aguardar um momento para garantir timestamp diferente
        from time import sleep
        sleep(1)

        # Adicionar livro à estante do usuário
        new_book = Book.objects.create(
            titulo='New Sci-Fi Book',
            autor='Isaac Asimov',
            genero='Ficção Científica',
            categoria='Ficção',
            temas='robôs,tecnologia,futuro'
        )
        UserBookShelf.objects.create(
            user=self.user1,
            book=new_book,
            shelf_type='lido'
        )

        # Forçar invalidação do cache
        engine.invalidate_recommendations_cache(self.user1)

        # Obter novas recomendações
        new_recommendations = engine.get_recommendations(self.user1, limit=3)
        new_ids = set(new_recommendations.values_list('id', flat=True))

        # Verificar se as recomendações mudaram
        self.assertNotEqual(
            initial_ids,
            new_ids,
            "As recomendações devem mudar após adicionar novo livro"
        )

        # Verificar se o livro adicionado não está nas recomendações
        self.assertNotIn(
            new_book.id,
            new_ids,
            "O livro recém adicionado não deve aparecer nas recomendações"
        )
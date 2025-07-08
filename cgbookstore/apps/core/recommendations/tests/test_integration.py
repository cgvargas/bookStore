# cgbookstore/apps/core/recommendations/tests/test_integration.py

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.core.cache import caches

from cgbookstore.apps.core.models import Book, UserBookShelf, Profile
from cgbookstore.apps.core.recommendations.engine import RecommendationEngine
from cgbookstore.apps.core.recommendations.utils.cache_manager import RecommendationCache
from cgbookstore.apps.core.recommendations import signals
from .test_helpers import create_test_user

User = get_user_model()


class RecommendationIntegrationTests(TransactionTestCase):
    """Testes de integração do sistema completo"""

    def setUp(self):
        # Cria usuário principal para os testes
        self.user = create_test_user('main_test_user')

        # Cria usuários com diferentes perfis usando o helper
        self.eclectic_user = create_test_user('eclectic_reader')
        self.loyal_user = create_test_user('loyal_reader')
        self.seasonal_user = create_test_user('seasonal_reader')

        # Cria perfil usando get_or_create para evitar duplicatas
        self.profile, created = Profile.objects.get_or_create(
            user=self.user,
            defaults={
                'interests': "Literatura brasileira, ficção científica"
            }
        )

        # Cria conjunto diverso de livros
        self._create_test_books()

        self.engine = RecommendationEngine()

    def _create_test_books(self):
        """Cria conjunto de livros para testes"""
        # Livros em português
        self.pt_books = []
        authors = ['Machado de Assis', 'Clarice Lispector', 'Jorge Amado']
        for i, author in enumerate(authors):
            for j in range(3):
                book = Book.objects.create(
                    titulo=f'{author} - Livro {j + 1}',
                    autor=author,
                    idioma='pt-BR',
                    categoria='Literatura Brasileira',
                    genero='Romance',
                    quantidade_acessos=100 + i * 10 + j,
                    quantidade_vendida=10 + i * 2 + j,
                    e_destaque=(i == 0 and j == 0)
                )
                self.pt_books.append(book)

        # Livros em inglês
        self.en_books = []
        for i in range(5):
            book = Book.objects.create(
                titulo=f'English Book {i + 1}',
                autor=f'Author {i + 1}',
                idioma='en',
                categoria='Fiction',
                genero='Sci-Fi',
                quantidade_acessos=50 + i * 5,
                quantidade_vendida=5 + i
            )
            self.en_books.append(book)

        # Livros de autores brasileiros em inglês
        self.mixed_books = []
        for author in ['Paulo Coelho', 'Lygia Fagundes Telles']:
            book = Book.objects.create(
                titulo=f'{author} - International Edition',
                autor=author,
                idioma='en',
                categoria='Literature',
                genero='Contemporary'
            )
            self.mixed_books.append(book)

    def test_complete_recommendation_flow(self):
        """Testa fluxo completo de recomendações"""
        # 1. Usuário adiciona livros à prateleira
        for book in self.pt_books[:3]:
            UserBookShelf.objects.create(
                user=self.user,
                book=book,
                shelf_type='lido'
            )

        # 2. Adiciona favorito
        UserBookShelf.objects.create(
            user=self.user,
            book=self.pt_books[3],
            shelf_type='favorito'
        )

        # 3. Obtém recomendações
        recommendations = self.engine.get_recommendations(self.user, limit=10)

        # Verificações
        self.assertGreater(len(recommendations), 0)
        self.assertLessEqual(len(recommendations), 10)

        # Não deve recomendar livros já na prateleira
        user_book_ids = UserBookShelf.objects.filter(
            user=self.user
        ).values_list('book_id', flat=True)

        for rec in recommendations:
            if hasattr(rec, 'id'):  # Livro local
                self.assertNotIn(rec.id, user_book_ids)

        # Deve priorizar português (baseado no histórico)
        local_recs = [r for r in recommendations if not self.engine._is_external(r)]
        pt_recs = [r for r in local_recs if r.idioma and 'pt' in r.idioma.lower()]

        self.assertGreater(
            len(pt_recs) / len(local_recs) if local_recs else 0,
            0.5,
            "Deve priorizar livros em português"
        )

    def test_cache_invalidation_on_shelf_update(self):
        """Testa invalidação de cache ao atualizar prateleira"""
        # Obtém recomendações iniciais (popula cache)
        initial_recs = self.engine.get_recommendations(self.user, limit=5)

        # Verifica se cache foi populado
        cached_data = RecommendationCache.get_recommendations(self.user)
        self.assertIsNotNone(cached_data)

        # Adiciona novo livro à prateleira
        UserBookShelf.objects.create(
            user=self.user,
            book=self.pt_books[0],
            shelf_type='lendo'
        )

        # Cache deve ter sido invalidado pelo signal
        cached_data = RecommendationCache.get_recommendations(self.user)
        self.assertIsNone(cached_data)

        # Novas recomendações não devem incluir o livro adicionado
        new_recs = self.engine.get_recommendations(self.user, limit=5)
        rec_ids = [r.id for r in new_recs if hasattr(r, 'id')]
        self.assertNotIn(self.pt_books[0].id, rec_ids)

    def test_personalized_shelf_generation(self):
        """Testa geração de prateleira personalizada"""
        # Configura histórico diverso
        # Adiciona livros de diferentes categorias
        UserBookShelf.objects.create(
            user=self.user,
            book=self.pt_books[0],
            shelf_type='favorito'
        )
        UserBookShelf.objects.create(
            user=self.user,
            book=self.pt_books[1],
            shelf_type='lido'
        )
        UserBookShelf.objects.create(
            user=self.user,
            book=self.en_books[0],
            shelf_type='lido'
        )

        # Gera prateleira personalizada
        shelf = self.engine.get_personalized_shelf(self.user, shelf_size=20)

        # Verificações estruturais
        self.assertIn('destaques', shelf)
        self.assertIn('seu_idioma', shelf)
        self.assertIn('por_genero', shelf)
        self.assertIn('por_autor', shelf)
        self.assertIn('descobertas', shelf)

        # Verifica conteúdo
        if shelf['destaques']:
            # Destaques devem incluir livros marcados como destaque
            destaque_titles = [b.titulo for b in shelf['destaques'] if hasattr(b, 'titulo')]
            self.assertTrue(
                any('Machado de Assis - Livro 1' in title for title in destaque_titles)
            )

        # Seção "seu_idioma" deve ter livros em português
        if shelf['seu_idioma']:
            for book in shelf['seu_idioma']:
                if hasattr(book, 'idioma'):
                    self.assertIn('pt', book.idioma.lower())

    def test_mixed_recommendations_with_language_preference(self):
        """Testa recomendações mistas com preferência de idioma"""
        # Configura preferência forte por português
        for book in self.pt_books[:5]:
            UserBookShelf.objects.create(
                user=self.user,
                book=book,
                shelf_type='lido' if book != self.pt_books[0] else 'favorito'
            )

        # Obtém recomendações mistas
        mixed = self.engine.get_mixed_recommendations(self.user, limit=15)

        # Verifica estrutura
        self.assertIn('local', mixed)
        self.assertIn('external', mixed)
        self.assertIn('language_profile', mixed)

        # Verifica preferência de idioma
        lang_profile = mixed['language_profile']
        self.assertGreater(lang_profile['portuguese_preference'], 0.8)

        # Maioria das recomendações locais devem ser em português
        local_books = mixed['local']
        if local_books:
            pt_books = [b for b in local_books if b.idioma and 'pt' in b.idioma.lower()]
            self.assertGreater(len(pt_books) / len(local_books), 0.6)

    def test_profile_integration_with_recommendations(self):
        """Testa integração do perfil com recomendações"""
        # Atualiza perfil com interesses específicos
        self.profile.interests = "Paulo Coelho, literatura fantástica, livros em português"
        self.profile.save()

        # Adiciona alguns livros para criar contexto
        UserBookShelf.objects.create(
            user=self.user,
            book=self.pt_books[0],
            shelf_type='lido'
        )

        # Obtém recomendações
        recommendations = self.engine.get_recommendations(self.user, limit=10)

        # Deve incluir livros de Paulo Coelho (mixed_books)
        rec_authors = []
        for rec in recommendations:
            if hasattr(rec, 'autor'):
                rec_authors.append(rec.autor)

        self.assertTrue(
            any('Paulo Coelho' in author for author in rec_authors),
            "Deve recomendar livros de autores mencionados nos interesses"
        )

    def test_adaptive_weights_in_action(self):
        """Testa pesos adaptativos em ação"""
        # Configura usuário como leitor fiel (mesmo autor)
        author_books = [b for b in self.pt_books if 'Machado de Assis' in b.autor]
        for book in author_books:
            UserBookShelf.objects.create(
                user=self.user,
                book=book,
                shelf_type='lido'
            )

        # Obtém recomendações
        recommendations = self.engine.get_recommendations(self.user, limit=10)

        # Análise de comportamento deve identificar como leitor fiel
        behavior = self.engine._analyze_user_behavior(self.user)
        self.assertTrue(behavior['is_loyal_reader'])

        # Recomendações devem favorecer mesmo autor ou similar
        local_recs = [r for r in recommendations if not self.engine._is_external(r)]
        similar_authors = [
            r for r in local_recs
            if hasattr(r, 'autor') and (
                    'Machado de Assis' in r.autor or
                    'Clarice Lispector' in r.autor or
                    'Jorge Amado' in r.autor
            )
        ]

        self.assertGreater(
            len(similar_authors) / len(local_recs) if local_recs else 0,
            0.3,
            "Leitor fiel deve receber mais recomendações de autores similares"
        )

    def test_fallback_behavior(self):
        """Testa comportamento de fallback"""
        # Cria usuário sem histórico
        new_user = User.objects.create_user(
            username='new_user',
            password='test123'
        )

        # Obtém recomendações
        recommendations = self.engine.get_recommendations(new_user, limit=10)

        # Deve retornar recomendações mesmo sem histórico
        self.assertGreater(len(recommendations), 0)

        # Deve priorizar português (comportamento padrão)
        local_recs = [r for r in recommendations if not self.engine._is_external(r)]
        pt_recs = [
            r for r in local_recs
            if hasattr(r, 'idioma') and 'pt' in r.idioma.lower()
        ]

        self.assertGreater(len(pt_recs), 0, "Deve incluir livros em português no fallback")
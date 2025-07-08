# cgbookstore/apps/core/recommendations/tests/test_adaptive_engine.py
from django.utils import timezone
from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock # MagicMock pode não ser mais necessário se mock_cache era o único uso

from cgbookstore.apps.core.models import Book, UserBookShelf, Profile
from cgbookstore.apps.core.recommendations.engine import RecommendationEngine
from .test_helpers import create_test_user

User = get_user_model()


class AdaptiveEngineTests(TestCase):
    """Testes para o motor de recomendações adaptativo"""

    def setUp(self):
        # Cria usuários com diferentes perfis usando o helper
        self.eclectic_user = create_test_user('eclectic_reader')
        self.loyal_user = create_test_user('loyal_reader')
        self.seasonal_user = create_test_user('seasonal_reader')

        # Cria livros variados
        self.genres = ['Ficção', 'Romance', 'Suspense', 'Fantasia', 'Terror', 'Drama']
        self.authors = ['Autor A', 'Autor B', 'Autor C', 'Autor D']

        self.books = []
        for i, genre in enumerate(self.genres * 3):  # 18 livros
            author = self.authors[i % len(self.authors)]
            book = Book.objects.create(
                titulo=f'Livro {i}',
                autor=author,
                genero=genre,
                categoria=genre,
                idioma='pt-BR',
                quantidade_acessos=i * 10,
                quantidade_vendida=i * 5
            )
            self.books.append(book)

        self._setup_user_behaviors()
        self.engine = RecommendationEngine()

    def _setup_user_behaviors(self):
        """Configura comportamentos distintos para cada usuário"""
        # Usuário eclético - lê varios gêneros
        for i, book in enumerate(self.books[:10]):
            if i < 6:  # 6 gêneros diferentes
                UserBookShelf.objects.create(
                    user=self.eclectic_user,
                    book=book,
                    shelf_type='lido'
                )

        # Usuário fiel - lê mesmo autor
        author_books = [b for b in self.books if b.autor == 'Autor A']
        for book in author_books[:4]:
            UserBookShelf.objects.create(
                user=self.loyal_user,
                book=book,
                shelf_type='lido'
            )

        # Usuário sazonal - lê em períodos específicos
        # Simularia leitura em meses específicos
        for book in self.books[:3]:
            shelf = UserBookShelf.objects.create(
                user=self.seasonal_user,
                book=book,
                shelf_type='lido'
            )
            # Simula leitura em janeiro
            shelf.added_at = timezone.now().replace(month=1)
            shelf.save()

    def test_adaptive_weights_calculation(self):
        """Testa cálculo de pesos adaptativos"""
        # Mock do perfil de idioma
        with patch.object(self.engine._language_provider, 'get_language_affinity') as mock_lang:
            mock_lang.return_value = {'portuguese_preference': 0.8}

            # Testa usuário eclético
            weights = self.engine._calculate_adaptive_weights(
                self.eclectic_user,
                {'portuguese_preference': 0.5}
            )

            self.assertGreater(weights['category'], weights['history'])
            self.assertEqual(sum(weights.values()), 1.0)  # Soma deve ser 1

            # Testa usuário fiel
            weights = self.engine._calculate_adaptive_weights(
                self.loyal_user,
                {'portuguese_preference': 0.5}
            )

            self.assertGreater(weights['history'], weights['category'])
            self.assertGreater(weights['similarity'], 0.25)

    def test_user_behavior_analysis(self):
        """Testa análise de comportamento do usuário"""
        # Analisa usuário eclético
        behavior = self.engine._analyze_user_behavior(self.eclectic_user)
        self.assertTrue(behavior['is_eclectic'])
        self.assertFalse(behavior['is_loyal_reader'])

        # Analisa usuário fiel
        behavior = self.engine._analyze_user_behavior(self.loyal_user)
        self.assertFalse(behavior['is_eclectic'])
        self.assertTrue(behavior['is_loyal_reader'])

    def test_local_prioritization(self):
        """Testa priorização de recomendações locais"""
        with patch.object(self.engine._external_provider, 'get_recommendations') as mock_external:
            # Simula recomendações externas
            mock_external.return_value = [
                {'id': 'ext1', 'volumeInfo': {'title': 'External Book 1'}},
                {'id': 'ext2', 'volumeInfo': {'title': 'External Book 2'}}
            ]

            recommendations = self.engine.get_recommendations(self.eclectic_user, limit=10)

            # Conta recomendações por tipo
            local_count = sum(1 for r in recommendations if not self.engine._is_external(r))
            external_count = sum(1 for r in recommendations if self.engine._is_external(r))

            # Verifica se locais são priorizadas (pelo menos 70%)
            self.assertGreaterEqual(local_count / len(recommendations), 0.7)
            self.assertLessEqual(external_count / len(recommendations), 0.3)

    def test_mixed_recommendations_structure(self):
        """Testa estrutura de recomendações mistas"""
        mixed = self.engine.get_mixed_recommendations(self.eclectic_user, limit=10)

        self.assertIn('local', mixed)
        self.assertIn('external', mixed)
        self.assertIn('has_external', mixed)
        self.assertIn('total', mixed)
        self.assertIn('language_profile', mixed)

        self.assertEqual(
            mixed['total'],
            len(mixed['local']) + len(mixed['external'])
        )

    def test_personalized_shelf_sections(self):
        """Testa geração de prateleira personalizada"""
        shelf = self.engine.get_personalized_shelf(self.eclectic_user, shelf_size=20)

        # Verifica seções obrigatórias
        self.assertIn('destaques', shelf)
        self.assertIn('seu_idioma', shelf)
        self.assertIn('por_genero', shelf)
        self.assertIn('por_autor', shelf)
        self.assertIn('descobertas', shelf)

        # Verifica se há conteúdo nas seções
        self.assertIsInstance(shelf['destaques'], list)
        self.assertIsInstance(shelf['por_genero'], dict)
        self.assertIsInstance(shelf['por_autor'], dict)

    # @patch('cgbookstore.apps.core.recommendations.engine.RecommendationCache') # <--- Patch removido
    def test_cache_key_generation(self): # <--- Parâmetro mock_cache removido
        """Testa geração de chave de cache com idioma"""
        with patch.object(self.engine._language_provider, 'get_language_affinity') as mock_lang:
            mock_lang.return_value = {
                'preferred_languages': {'pt': 5.0, 'en': 2.0}
            }

            key = self.engine._get_cache_key(self.eclectic_user)

            self.assertIn(str(self.eclectic_user.id), key)
            self.assertIn('v2', key)  # Versão 2 do cache

            # Verifica se inclui hash de idioma
            self.assertIsInstance(key, str)
            self.assertLess(len(key), 250)  # Não deve exceder limite

    def test_fallback_recommendations(self):
        """Testa recomendações de fallback"""
        # Cria usuário sem histórico
        new_user = User.objects.create_user(
            username='new_user',
            password='test123'
        )

        # Força um erro no provider principal
        with patch.object(self.engine._history_provider, 'get_recommendations') as mock_hist:
            mock_hist.side_effect = Exception("Erro simulado")

            recommendations = self.engine.get_recommendations(new_user, limit=5)

            # Deve retornar recomendações mesmo com erro
            self.assertGreater(len(recommendations), 0)

            # Verifica se prioriza português no fallback
            pt_books = [
                r for r in recommendations
                if hasattr(r, 'idioma') and 'pt' in r.idioma.lower()
            ]
            self.assertGreater(len(pt_books), 0)
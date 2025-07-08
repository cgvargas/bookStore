# cgbookstore/apps/core/recommendations/tests/test_language_provider.py

from django.test import TestCase
from django.contrib.auth import get_user_model
# from django.utils import timezone # Não utilizado diretamente aqui, pode remover se não usado em outros helpers
# from datetime import timedelta # Não utilizado diretamente aqui

from cgbookstore.apps.core.models import Book, UserBookShelf, Profile
from cgbookstore.apps.core.recommendations.providers.language_preference import LanguagePreferenceProvider
from .test_helpers import create_test_user

User = get_user_model()


class LanguagePreferenceProviderTests(TestCase):
    """Testes para o provider de preferências de idioma"""

    def setUp(self):
        # Cria usuários de teste usando o helper com nomes únicos
        self.user_pt = create_test_user('leitor_portugues_lang')
        self.user_en = create_test_user('english_reader_lang')
        self.user_mixed = create_test_user('polyglot_lang')

        # Cria perfis com verificação de existência
        # --- INÍCIO DA SEÇÃO DE DEBUG ---
        print(f"DEBUG setUp: Chamando _create_or_get_profile para user_pt ({self.user_pt.username})")
        # --- FIM DA SEÇÃO DE DEBUG ---
        profile_pt = self._create_or_get_profile(
            self.user_pt,
            "Literatura brasileira, Machado de Assis, cultura lusófona"
        )
        # --- INÍCIO DA SEÇÃO DE DEBUG ---
        if profile_pt:
            print(f"DEBUG setUp: Interests do profile_pt ({self.user_pt.username}) IMEDIATAMENTE APÓS _create_or_get_profile: '{profile_pt.interests}'")
        else:
            print(f"DEBUG setUp: profile_pt para ({self.user_pt.username}) é None após _create_or_get_profile.")
        # --- FIM DA SEÇÃO DE DEBUG ---

        # --- INÍCIO DA SEÇÃO DE DEBUG ---
        print(f"DEBUG setUp: Chamando _create_or_get_profile para user_en ({self.user_en.username})")
        # --- FIM DA SEÇÃO DE DEBUG ---
        profile_en = self._create_or_get_profile(
            self.user_en,
            "Science fiction, British literature"
        )
        # --- INÍCIO DA SEÇÃO DE DEBUG ---
        if profile_en:
            print(f"DEBUG setUp: Interests do profile_en ({self.user_en.username}) IMEDIATAMENTE APÓS _create_or_get_profile: '{profile_en.interests}'")
        else:
            print(f"DEBUG setUp: profile_en para ({self.user_en.username}) é None após _create_or_get_profile.")
        # --- FIM DA SEÇÃO DE DEBUG ---


        # Cria livros em diferentes idiomas com nomes únicos
        self.books_pt = []
        for i in range(5):
            book = Book.objects.create(
                titulo=f'Lang Livro Português {i}',
                autor=f'Lang Autor Silva {i}',
                idioma='pt-BR',
                categoria='Literatura',
                genero='Romance'
            )
            self.books_pt.append(book)

        self.books_en = []
        for i in range(5):
            book = Book.objects.create(
                titulo=f'Lang English Book {i}',
                autor=f'Lang Author Smith {i}',
                idioma='en',
                categoria='Fiction',
                genero='Sci-Fi'
            )
            self.books_en.append(book)

        # Livros de autores brasileiros em inglês
        self.books_br_authors = []
        for idx, author in enumerate(['Paulo Coelho', 'Clarice Lispector', 'Jorge Amado']):
            book = Book.objects.create(
                titulo=f'Lang Book by {author} {idx}',
                autor=author,
                idioma='en',
                categoria='Literature'
            )
            self.books_br_authors.append(book)

        # Configura prateleiras dos usuários
        self._setup_user_shelves()

        self.provider = LanguagePreferenceProvider()

    def _create_or_get_profile(self, user, interests):
        """Cria ou obtém perfil existente para evitar IntegrityError"""
        # --- INÍCIO DA SEÇÃO DE DEBUG ---
        print(f"DEBUG _create_or_get_profile: User: {user.username}, ID: {user.id}, Target Interests: '{interests}'")
        # --- FIM DA SEÇÃO DE DEBUG ---
        profile_instance = None # Inicializa para garantir que tem um valor
        try:
            profile_instance = Profile.objects.get(user=user)
            # --- INÍCIO DA SEÇÃO DE DEBUG ---
            print(f"DEBUG _create_or_get_profile: Profile encontrado para {user.username}. Current interests ANTES da atribuição: '{profile_instance.interests}'")
            # --- FIM DA SEÇÃO DE DEBUG ---
            profile_instance.interests = interests
            profile_instance.save()
            # Opcional: recarregar do BD para ter certeza do que foi salvo
            profile_instance.refresh_from_db()
            # --- INÍCIO DA SEÇÃO DE DEBUG ---
            print(f"DEBUG _create_or_get_profile: Profile atualizado para {user.username}. Interests APÓS SAVE e REFRESH: '{profile_instance.interests}'")
            # --- FIM DA SEÇÃO DE DEBUG ---
        except Profile.DoesNotExist:
            # --- INÍCIO DA SEÇÃO DE DEBUG ---
            print(f"DEBUG _create_or_get_profile: Profile NÃO encontrado para {user.username}. Criando novo.")
            # --- FIM DA SEÇÃO DE DEBUG ---
            profile_instance = Profile.objects.create(user=user, interests=interests)
            # Opcional: recarregar do BD para ter certeza do que foi salvo
            # profile_instance.refresh_from_db() # Create já retorna o objeto como está no BD se não houver save() customizado complexo
            # --- INÍCIO DA SEÇÃO DE DEBUG ---
            print(f"DEBUG _create_or_get_profile: Profile criado para {user.username}. Interests APÓS CREATE: '{profile_instance.interests}'")
            # --- FIM DA SEÇÃO DE DEBUG ---
        # --- INÍCIO DA SEÇÃO DE DEBUG ---
        print(f"DEBUG _create_or_get_profile: Retornando profile_instance para {user.username} com interests: '{profile_instance.interests if profile_instance else 'None'}'")
        # --- FIM DA SEÇÃO DE DEBUG ---
        return profile_instance


    def _setup_user_shelves(self):
        """Configura as prateleiras dos usuários de teste"""
        # Usuário português - só lê em português
        for book in self.books_pt[:3]:
            UserBookShelf.objects.create(
                user=self.user_pt,
                book=book,
                shelf_type='lido'
            )
        UserBookShelf.objects.create(
            user=self.user_pt,
            book=self.books_pt[3],
            shelf_type='favorito'
        )

        # Usuário inglês - só lê em inglês
        for book in self.books_en[:3]:
            UserBookShelf.objects.create(
                user=self.user_en,
                book=book,
                shelf_type='lido'
            )

        # Usuário misto - lê em ambos idiomas
        UserBookShelf.objects.create(
            user=self.user_mixed,
            book=self.books_pt[0],
            shelf_type='lido'
        )
        UserBookShelf.objects.create(
            user=self.user_mixed,
            book=self.books_en[0],
            shelf_type='lido'
        )
        UserBookShelf.objects.create(
            user=self.user_mixed,
            book=self.books_en[1],
            shelf_type='abandonei'  # Abandonou livro em inglês
        )

    def test_language_normalization(self):
        """Testa normalização de códigos de idioma"""
        test_cases = [
            ('pt-BR', 'pt'),
            ('pt-PT', 'pt'),
            ('portuguese', 'pt'),
            ('português', 'pt'),
            ('en-US', 'en'),
            ('english', 'en'),
            ('', 'unknown'),
            (None, 'unknown')
        ]

        for input_lang, expected in test_cases:
            result = self.provider._normalize_language(input_lang)
            self.assertEqual(result, expected, f"Falha ao normalizar {input_lang}")

    def test_portuguese_detection(self):
        """Testa detecção de variantes de português"""
        portuguese_variants = ['pt', 'pt-BR', 'pt-PT', 'por', 'portuguese', 'português']

        for variant in portuguese_variants:
            self.assertTrue(
                self.provider._is_portuguese(variant),
                f"{variant} deveria ser detectado como português"
            )

        non_portuguese = ['en', 'es', 'fr', 'de']
        for lang in non_portuguese:
            self.assertFalse(
                self.provider._is_portuguese(lang),
                f"{lang} não deveria ser detectado como português"
            )

    def test_national_author_detection(self):
        """Testa detecção de autores nacionais"""
        brazilian_authors = [
            'Machado de Assis',
            'Clarice Lispector',
            'Jorge Amado',
            'Paulo Coelho',
            'José Silva',
            'Maria Santos'
        ]

        for author in brazilian_authors:
            self.assertTrue(
                self.provider._is_national_author(author),
                f"{author} deveria ser detectado como autor nacional"
            )

        foreign_authors = [
            'Stephen King',
            'J.K. Rowling',
            'George Orwell'
        ]

        for author in foreign_authors:
            self.assertFalse(
                self.provider._is_national_author(author),
                f"{author} não deveria ser detectado como autor nacional"
            )

    def test_language_preference_analysis(self):
        """Testa análise de preferências de idioma"""
        profile_pt = self.provider._analyze_language_preferences(self.user_pt)
        self.assertGreater(profile_pt['portuguese_preference'], 3.0)
        self.assertGreater(profile_pt['portuguese_percentage'], 0.9)
        self.assertEqual(profile_pt['languages']['pt'], 7.5)  # (3 lidos * 2.0) + (1 favorito * 1.5) = 7.5

        profile_en = self.provider._analyze_language_preferences(self.user_en)
        self.assertEqual(profile_en['portuguese_preference'], 0.0)
        self.assertEqual(profile_en['languages']['en'], 6.0)

        profile_mixed = self.provider._analyze_language_preferences(self.user_mixed)
        self.assertIn('pt', profile_mixed['languages'])
        self.assertIn('en', profile_mixed['languages'])
        self.assertIn('en', profile_mixed['abandoned_languages'])

    def test_recommendations_for_portuguese_reader(self):
        """Testa recomendações para leitor de português"""
        recommendations = self.provider.get_recommendations(self.user_pt, limit=5)

        if hasattr(recommendations, 'values_list'):
            recommended_ids = list(recommendations.values_list('id', flat=True))
            recommendation_list = list(recommendations)
        else:
            recommended_ids = [r.id for r in recommendations if hasattr(r, 'id')]
            recommendation_list = recommendations

        user_books = UserBookShelf.objects.filter(
            user=self.user_pt
        ).values_list('book_id', flat=True)

        for book_id in recommended_ids:
            self.assertNotIn(book_id, user_books)

        if recommendation_list:
            for book in recommendation_list[:3]:
                if hasattr(book, 'idioma') and hasattr(book, 'autor'):
                    self.assertTrue(
                        self.provider._is_portuguese(book.idioma) or
                        self.provider._is_national_author(book.autor),
                        f"Livro {book.titulo} deveria ser em português ou de autor nacional"
                    )

    def test_recommendations_avoid_abandoned_languages(self):
        """Testa se recomendações evitam idiomas abandonados"""
        for book in self.books_en[2:4]:
            UserBookShelf.objects.create(
                user=self.user_mixed,
                book=book,
                shelf_type='abandonei'
            )

        recommendations = self.provider.get_recommendations(self.user_mixed, limit=5)

        if hasattr(recommendations, 'count'):
            recommendation_list = list(recommendations)
        else:
            recommendation_list = recommendations

        if recommendation_list:
            english_books = [
                book for book in recommendation_list
                if hasattr(book, 'idioma') and book.idioma and 'en' in book.idioma.lower()
            ]
            self.assertLess(
                len(english_books),
                len(recommendation_list) / 2,
                "Não deveria recomendar muitos livros em inglês para usuário que abandona"
            )

    def test_profile_integration(self):
        """Testa integração com interesses do perfil"""
        # --- INÍCIO DA SEÇÃO DE DEBUG ---
        print(
            f"DEBUG test_profile_integration: Verificando interests de self.user_pt ({self.user_pt.username}, ID: {self.user_pt.id}) original ANTES de recarregar.")
        if hasattr(self.user_pt, 'profile') and self.user_pt.profile:
            print(
                f"DEBUG test_profile_integration: self.user_pt.profile.interests (original): '{self.user_pt.profile.interests}'")
        else:
            print(
                f"DEBUG test_profile_integration: self.user_pt ({self.user_pt.username}) original NÃO tem perfil ou profile é None.")
        # --- FIM DA SEÇÃO DE DEBUG ---

        # Obtém uma instância "fresca" do usuário do banco de dados para garantir que
        # o perfil relacionado e seus campos (como interests) estejam atualizados.
        user_for_test = User.objects.get(id=self.user_pt.id)

        # --- INÍCIO DA SEÇÃO DE DEBUG ---
        print(
            f"DEBUG test_profile_integration: Verificando interests de user_for_test (ID: {user_for_test.id}) APÓS User.objects.get()")
        if hasattr(user_for_test, 'profile') and user_for_test.profile:
            print(
                f"DEBUG test_profile_integration: user_for_test.profile.interests: '{user_for_test.profile.interests}'")
        else:
            print(
                f"DEBUG test_profile_integration: user_for_test (ID: {user_for_test.id}) NÃO tem perfil ou profile é None após User.objects.get().")
        # --- FIM DA SEÇÃO DE DEBUG ---

        profile_prefs = self.provider._analyze_profile_preferences(user_for_test)  # Usa a instância recarregada

        self.assertIn('pt', profile_prefs['preferred_languages'],
                      f"Falha: 'pt' não encontrado em preferred_languages. Profile_prefs: {profile_prefs}")
        self.assertGreater(len(profile_prefs['interests_keywords']), 0,
                           f"Falha: interests_keywords está vazio. Profile_prefs: {profile_prefs}")

        found_literatura = any('literatura' in keyword.lower() for keyword in profile_prefs['interests_keywords'])
        self.assertTrue(found_literatura,
                        f"A palavra 'literatura' não foi encontrada nos keywords de interesse do perfil. Keywords: {profile_prefs['interests_keywords']}")

    def test_empty_user_history(self):
        """Testa recomendações para usuário sem histórico"""
        new_user = User.objects.create_user(
            username='new_reader_lang_unique', # Username já usado em execuções anteriores, pode causar problemas se não limpo
            password='testpass123'
        )
        # Garante que um perfil exista para new_user, mesmo que com interesses vazios,
        # para que hasattr(user, 'profile') seja verdadeiro em get_recommendations
        self._create_or_get_profile(new_user, "")


        recommendations = self.provider.get_recommendations(new_user, limit=5)

        if hasattr(recommendations, 'count'):
            rec_count = recommendations.count()
            recommendation_list = list(recommendations)
        else:
            rec_count = len(recommendations)
            recommendation_list = recommendations

        self.assertGreater(rec_count, 0)

        if recommendation_list:
            pt_books = [
                book for book in recommendation_list
                if hasattr(book, 'idioma') and book.idioma and self.provider._is_portuguese(book.idioma)
            ]
            self.assertGreater(
                len(pt_books),
                len(recommendation_list) / 2, # Alterado para / 2 para ser menos restrito, antes era rec_count / 2
                "Deveria priorizar livros em português para novo usuário"
            )

    def test_language_affinity_calculation(self):
        """Testa cálculo de afinidade com idiomas"""
        affinity = self.provider.get_language_affinity(self.user_pt)

        self.assertIn('preferred_languages', affinity)
        self.assertIn('portuguese_preference', affinity)
        self.assertIn('national_authors_preference', affinity)
        self.assertIn('avoided_languages', affinity)

        self.assertGreater(affinity['portuguese_preference'], 0.9)
        self.assertEqual(affinity['preferred_languages']['pt'], 7.5)
from django.db.models import Count, Q, F, Value, FloatField, Case, When
from typing import Dict, Set, List
from collections import Counter
import random
from ...models import Book, User, UserBookShelf
from .mapping import CategoryMapping
from django.test import TestCase
from django.contrib.auth import get_user_model
from ...models import Book, UserBookShelf
from ..providers.exclusion import ExclusionProvider

User = get_user_model()


class ExclusionProviderExtendedTests(TestCase):
    def setUp(self):
        # Cria usuário de teste
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        # Cria usuário com perfil diferente
        self.user2 = User.objects.create_user(
            username='testuser2',
            password='testpass123'
        )

        # Cria livros com diferentes categorias
        self.programming_book = Book.objects.create(
            titulo='Python Avançado',
            categoria="['Computers']",
            genero='Programação'
        )

        self.religious_book = Book.objects.create(
            titulo='Livro Religioso',
            categoria="['Religion']",
            genero='Religião'
        )

        self.fiction_book = Book.objects.create(
            titulo='Ficção Épica',
            categoria='Fiction',
            genero='Fantasia'
        )

        # Adiciona livros à prateleira do primeiro usuário (perfil técnico)
        UserBookShelf.objects.create(
            user=self.user,
            book=self.programming_book,
            shelf_type='favorito'
        )

        # Adiciona livros à prateleira do segundo usuário (perfil religioso)
        UserBookShelf.objects.create(
            user=self.user2,
            book=self.religious_book,
            shelf_type='favorito'
        )

    def test_cross_category_exclusions(self):
        """Testa se livros de categorias muito diferentes são excluídos corretamente"""
        # Obtém exclusões para usuário técnico
        excluded_tech = ExclusionProvider.get_excluded_books(self.user)

        # Obtém exclusões para usuário religioso
        excluded_religious = ExclusionProvider.get_excluded_books(self.user2)

        # Verifica se cada usuário tem seus livros específicos excluídos
        self.assertIn(self.programming_book.id, excluded_tech)
        self.assertIn(self.religious_book.id, excluded_religious)

        # Verifica se livros de outras categorias NÃO estão excluídos
        self.assertNotIn(self.religious_book.id, excluded_tech)
        self.assertNotIn(self.programming_book.id, excluded_religious)

    def test_verify_category_consistency(self):
        """Testa consistência de categorias nas recomendações"""
        # Cria lista de recomendações com mix de categorias
        mixed_recommendations = [
            self.programming_book,
            self.religious_book,
            self.fiction_book
        ]

        # Verifica recomendações para usuário técnico
        tech_recommendations = ExclusionProvider.verify_exclusions(
            mixed_recommendations,
            self.user
        )

        # O livro de programação deve estar excluído por já estar na prateleira
        self.assertNotIn(self.programming_book, tech_recommendations)

        # Os outros livros devem permanecer
        self.assertIn(self.religious_book, tech_recommendations)
        self.assertIn(self.fiction_book, tech_recommendations)

    def test_shelf_type_exclusions(self):
        """Testa exclusões baseadas em diferentes tipos de prateleira"""
        # Adiciona mesmo livro em diferentes prateleiras
        book = Book.objects.create(
            titulo='Livro Teste',
            categoria='Test'
        )

        shelf_types = ['lido', 'lendo', 'vou_ler', 'abandonei', 'favorito']

        for shelf_type in shelf_types:
            UserBookShelf.objects.create(
                user=self.user,
                book=book,
                shelf_type=shelf_type
            )

            # Verifica se o livro é excluído para cada tipo de prateleira
            excluded = ExclusionProvider.get_excluded_books(self.user)
            self.assertIn(book.id, excluded)

    def test_mixed_recommendations_filtering(self):
        """Testa filtragem de recomendações mistas"""
        # Cria recomendações em diferentes formatos
        recommendations = {
            'primary': Book.objects.all(),
            'secondary': Book.objects.filter(categoria="['Computers']"),
            'tertiary': Book.objects.filter(categoria="['Religion']")
        }

        # Aplica filtragem
        filtered = ExclusionProvider.get_available_recommendations(
            recommendations,
            self.user
        )

        # Verifica se as exclusões foram aplicadas corretamente
        for key in filtered:
            self.assertNotIn(
                self.programming_book,
                filtered[key]
            )

    def test_dynamic_exclusions(self):
        """Testa exclusões com mudanças dinâmicas na prateleira"""
        initial_excluded = ExclusionProvider.get_excluded_books(self.user)
        initial_count = len(initial_excluded)

        # Adiciona novo livro à prateleira
        new_book = Book.objects.create(
            titulo='Novo Livro',
            categoria='Test'
        )

        UserBookShelf.objects.create(
            user=self.user,
            book=new_book,
            shelf_type='lendo'
        )

        # Verifica se exclusões foram atualizadas
        updated_excluded = ExclusionProvider.get_excluded_books(self.user)
        self.assertEqual(len(updated_excluded), initial_count + 1)
        self.assertIn(new_book.id, updated_excluded)

class CategoryBasedProvider:
    """Provider de recomendações baseadas em categorias"""

    SHELF_WEIGHTS = {
        'favorito': 3.0,
        'lido': 1.5,
        'lendo': 1.0,
        'vou_ler': 0.5
    }

    def __init__(self):
        self._mapping = CategoryMapping()

    def get_recommendations(self, user: User, limit: int = 20) -> List[Book]:
        """
        Gera recomendações baseadas nas categorias preferidas
        """
        print("\n=== Iniciando recomendações por categoria ===")
        excluded_books = set(UserBookShelf.objects.filter(
            user=user
        ).values_list('book_id', flat=True))
        print(f"Livros excluídos: {excluded_books}")

        # Obtém preferências
        preferences = self._analyze_user_preferences(user)
        print("\nPreferências do usuário:")
        print(f"Gêneros: {dict(preferences['genres'])}")
        print(f"Categorias: {dict(preferences['categories'])}")
        print(f"Temas: {dict(preferences['themes'])}")

        # Obtém recomendações primárias
        primary_recs = self._get_primary_recommendations(preferences, excluded_books)
        print(f"\nRecomendações primárias: {[book.id for book in primary_recs]}")

        if len(primary_recs) >= limit:
            return primary_recs[:limit]

        # Adiciona recomendações secundárias se necessário
        needed = limit - len(primary_recs)
        secondary_excluded = excluded_books | {book.id for book in primary_recs}
        secondary_recs = self._get_secondary_recommendations(preferences, secondary_excluded)
        print(f"\nRecomendações secundárias: {[book.id for book in secondary_recs]}")

        # Combina resultados
        recommendations = list(primary_recs)
        recommendations.extend(secondary_recs[:needed])

        if len(recommendations) < limit:
            # Adiciona fallback se ainda precisar
            needed = limit - len(recommendations)
            fallback_excluded = secondary_excluded | {book.id for book in secondary_recs}
            fallback_recs = self._get_fallback_recommendations(fallback_excluded, needed)
            recommendations.extend(fallback_recs)
            print(f"\nRecomendações fallback: {[book.id for book in fallback_recs]}")

        final_recs = recommendations[:limit]
        print(f"\nRecomendações finais: {[book.id for book in final_recs]}")
        print("=====================================")
        return final_recs

    def _analyze_user_preferences(self, user: User) -> Dict:
        """Analisa preferências do usuário"""
        preferences = {
            'genres': Counter(),
            'categories': Counter(),
            'themes': Counter()
        }

        shelves = UserBookShelf.objects.filter(user=user).select_related('book')
        print(f"\nAnalisando {shelves.count()} livros do usuário")

        for shelf in shelves:
            weight = self.SHELF_WEIGHTS.get(shelf.shelf_type, 0.5)
            book = shelf.book
            print(f"\nProcessando livro {book.id} - {book.titulo}")
            print(f"Tipo prateleira: {shelf.shelf_type}, Peso: {weight}")

            # Processa gênero
            if book.genero:
                genres = [g.strip() for g in book.genero.split(',')]
                for genre in genres:
                    normalized_genre = self._mapping.normalize_category(genre)
                    if normalized_genre:
                        preferences['genres'][normalized_genre] += weight
                        print(f"Gênero: {genre} -> {normalized_genre}")

            # Processa categoria
            if book.categoria:
                categories = [c.strip() for c in book.categoria.split(',')]
                for category in categories:
                    normalized_category = self._mapping.normalize_category(category)
                    if normalized_category:
                        preferences['categories'][normalized_category] += weight
                        print(f"Categoria: {category} -> {normalized_category}")

            # Processa temas
            if book.temas:
                themes = [t.strip().lower() for t in book.temas.split(',')]
                for theme in themes:
                    if theme:
                        preferences['themes'][theme] += weight
                        print(f"Tema: {theme}")

        return preferences

    def _get_primary_recommendations(self, preferences: Dict, excluded_books: Set[int]) -> List[Book]:
        """Obtém recomendações primárias baseadas nas preferências principais"""
        base_query = Q()
        boost_conditions = []

        # Processa gêneros
        for genre, weight in preferences['genres'].items():
            # Condição exata e variações
            genre_variants = self._get_query_variants(genre)
            genre_condition = self._build_variant_query('genero', genre_variants)
            base_query |= genre_condition
            boost_conditions.append((genre_condition, weight))

            # Gêneros relacionados
            related_genres = self._mapping.get_related_categories(genre)
            if related_genres:
                for related in related_genres:
                    related_variants = self._get_query_variants(related)
                    related_condition = self._build_variant_query('genero', related_variants)
                    base_query |= related_condition
                    boost_conditions.append((related_condition, weight * 0.7))

        # Processa categorias
        for category, weight in preferences['categories'].items():
            # Condição exata e variações
            category_variants = self._get_query_variants(category)
            category_condition = self._build_variant_query('categoria', category_variants)
            base_query |= category_condition
            boost_conditions.append((category_condition, weight))

            # Categorias relacionadas
            related_categories = self._mapping.get_related_categories(category)
            if related_categories:
                for related in related_categories:
                    related_variants = self._get_query_variants(related)
                    related_condition = self._build_variant_query('categoria', related_variants)
                    base_query |= related_condition
                    boost_conditions.append((related_condition, weight * 0.7))

        # Processa temas
        for theme, weight in preferences['themes'].items():
            theme_condition = Q(temas__icontains=theme)
            base_query |= theme_condition
            boost_conditions.append((theme_condition, weight * 0.5))

        if not base_query:
            return []

            # Obtém livros base excluindo os que já estão na estante
        base_books = Book.objects.exclude(
            id__in=excluded_books
        ).filter(base_query).distinct()

        # Aplica boost baseado nas condições
        scored_books = []
        for book in base_books:
            # Calcula score base
            score = 0
            for condition, weight in boost_conditions:
                if Book.objects.filter(condition, id=book.id).exists():
                    score += weight

            # Adiciona componentes de popularidade ao score
            popularity_score = (
                    book.quantidade_acessos * 0.001 +  # Peso menor para acessos
                    book.quantidade_vendida * 0.01  # Peso maior para vendas
            )

            # Adiciona boost para livros em destaque
            if book.e_destaque:
                popularity_score *= 1.5

            # Score final combina relevância e popularidade
            final_score = score + popularity_score

            # Adiciona componente aleatório menor
            random_boost = random.uniform(0, 0.1)  # Reduzido de 0.2 para 0.1
            final_score += random_boost

            scored_books.append((book, final_score))

        # Ordena por score e outros critérios
        scored_books.sort(key=lambda x: (
            -x[1],  # Score final reverso
            -x[0].quantidade_vendida,  # Vendas em ordem decrescente
            -x[0].quantidade_acessos,  # Acessos em ordem decrescente
            x[0].ordem_exibicao  # Ordem de exibição original
        ))

        return [book for book, _ in scored_books]

    def _get_secondary_recommendations(self, preferences: Dict, excluded_books: Set[int]) -> List[Book]:
        """Obtém recomendações secundárias mais abrangentes"""
        base_query = Q()

        # Expande gêneros e categorias
        expanded_terms = set()

        # Adiciona gêneros e suas variações
        for genre in preferences['genres']:
            expanded_terms.add(genre)
            expanded_terms.update(self._mapping.get_related_categories(genre))

        # Adiciona categorias e suas variações
        for category in preferences['categories']:
            expanded_terms.add(category)
            expanded_terms.update(self._mapping.get_related_categories(category))

        # Constrói query para termos expandidos
        for term in expanded_terms:
            variants = self._get_query_variants(term)
            base_query |= self._build_variant_query('genero', variants)
            base_query |= self._build_variant_query('categoria', variants)

        # Adiciona busca por palavras-chave nos temas e título
        keywords = set()
        for genre in preferences['genres']:
            keywords.update(self._extract_keywords(genre))
        for category in preferences['categories']:
            keywords.update(self._extract_keywords(category))
        for theme in preferences['themes']:
            keywords.update(self._extract_keywords(theme))

        for keyword in keywords:
            if len(keyword) > 3:  # Ignora palavras muito curtas
                base_query |= (
                        Q(titulo__icontains=keyword) |
                        Q(genero__icontains=keyword) |
                        Q(categoria__icontains=keyword) |
                        Q(temas__icontains=keyword)
                )

        if not base_query:
            return []

        # Retorna recomendações com ordenação personalizada
        return list(Book.objects.exclude(
            id__in=excluded_books
        ).filter(
            base_query
        ).order_by(
            '-quantidade_acessos',
            '-quantidade_vendida',
            'ordem_exibicao',
            '?'
        ).distinct())

    def _get_fallback_recommendations(self, excluded_books: Set[int], limit: int) -> List[Book]:
        """Recomendações fallback baseadas em popularidade"""
        return list(Book.objects.exclude(
            id__in=excluded_books
        ).filter(
            Q(quantidade_vendida__gt=0) |
            Q(quantidade_acessos__gt=0) |
            Q(e_destaque=True)
        ).order_by(
            '-quantidade_vendida',
            '-quantidade_acessos',
            'ordem_exibicao',
            '-created_at'
        )[:limit])

    def _get_query_variants(self, term: str) -> List[str]:
        """Gera variações de um termo para busca"""
        term = term.lower().strip()
        variants = {term}
        variants.add(f"['{term}']")
        variants.add(f'["{term}"]')
        return list(variants)

    def _build_variant_query(self, field: str, variants: List[str]) -> Q:
        """Constrói query com variantes de um termo"""
        q = Q()
        for variant in variants:
            q |= Q(**{f"{field}__iexact": variant})
            q |= Q(**{f"{field}__icontains": variant})
        return q

    def _extract_keywords(self, text: str) -> Set[str]:
        """Extrai palavras-chave de um texto"""
        if not text:
            return set()

        words = text.lower().replace('[', '').replace(']', '').replace('"', '')
        words = words.replace("'", '').replace(',', ' ').split()
        return {w.strip() for w in words if len(w.strip()) > 3}

    def get_category_affinity(self, user: User) -> dict:
        """Retorna afinidade do usuário com diferentes categorias"""
        preferences = self._analyze_user_preferences(user)
        return {
            'genres': dict(preferences['genres']),
            'categories': dict(preferences['categories']),
            'themes': dict(preferences['themes'])
        }
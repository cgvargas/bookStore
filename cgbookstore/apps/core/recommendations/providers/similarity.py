import random
from random import random, sample
from django.db.models import Q, Count, Case, When, Value, FloatField
from django.db.models.functions import Coalesce
from typing import List, Dict, Set
from django.forms import IntegerField
from ...models import Book, User, UserBookShelf
from typing import List, Set
from django.db.models import QuerySet, Q
from django.contrib.auth import get_user_model
from ...models import Book, UserBookShelf

User = get_user_model()


class SimilarityBasedProvider:
    """Provider para recomendações baseadas em similaridade entre livros"""

    # Pesos para cálculo de similaridade
    WEIGHTS = {
        'genero': 0.35,
        'autor': 0.30,
        'categoria': 0.20,
        'temas': 0.15
    }

    def get_recommendations(self, user: User, limit: int = 20) -> QuerySet:
        """
        Gera recomendações baseadas em similaridade com livros favoritos
        """
        # Obtém TODOS os livros que devem ser excluídos (incluindo favoritos)
        excluded_books = UserBookShelf.objects.filter(
            user=user
        ).values_list('book_id', flat=True).distinct()

        # Obtém apenas livros favoritos para base de similaridade
        user_books = UserBookShelf.objects.filter(
            user=user,
            shelf_type__in=['favorito', 'lido']
        ).select_related('book')

        if not user_books.exists():
            return Book.objects.none()

        # Obtém padrões dos livros do usuário
        patterns = {
            'genres': set(),
            'authors': set(),
            'categories': set()
        }

        for shelf in user_books:
            book = shelf.book
            if book.genero:
                patterns['genres'].add(book.genero)
            if book.autor:
                patterns['authors'].add(book.autor)
            if book.categoria:
                patterns['categories'].add(book.categoria)

        # Constrói query de similaridade
        similarity_query = Q()

        # Adiciona critérios por gênero
        if patterns['genres']:
            similarity_query |= Q(genero__in=patterns['genres'])

        # Adiciona critérios por autor
        if patterns['authors']:
            similarity_query |= Q(autor__in=patterns['authors'])

        # Adiciona critérios por categoria
        if patterns['categories']:
            similarity_query |= Q(categoria__in=patterns['categories'])

        # Se não há critérios, retorna vazio
        if not similarity_query:
            return Book.objects.none()

        # Aplica a query excluindo todos os livros na estante do usuário
        recommendations = Book.objects.filter(
            similarity_query
        ).exclude(
            id__in=excluded_books
        ).distinct()

        return recommendations.order_by('?')[:limit]

    def _get_user_patterns(self, user_books: QuerySet) -> dict:
        """Extrai padrões dos livros do usuário"""
        patterns = {
            'genres': set(),
            'authors': set(),
            'categories': set()
        }

        for shelf in user_books:
            book = shelf.book
            if book.genero:
                patterns['genres'].add(book.genero)
            if book.autor:
                patterns['authors'].add(book.autor)
            if book.categoria:
                patterns['categories'].add(book.categoria)

    def _get_base_books(self, user: User):
        """
        Obtém livros base para cálculo de similaridade
        """
        return UserBookShelf.objects.filter(
            user=user,
            shelf_type__in=['favorito', 'lido']
        ).select_related('book')

    def _adjust_weights_for_user(self, user: User) -> Dict[str, float]:
        """
        Ajusta pesos de similaridade baseado no perfil do usuário
        """
        weights = self.WEIGHTS.copy()
        user_preferences = self._analyze_user_preferences(user)

        # Obtém livros do usuário
        user_books = UserBookShelf.objects.filter(
            user=user,
            shelf_type__in=['lido', 'lendo', 'favorito']
        ).select_related('book')

        if not user_books.exists():
            return weights

        # Analisa padrões específicos do usuário
        genres = {}
        authors = {}
        categories = {}

        for shelf in user_books:
            book = shelf.book
            if book.genero:
                genres[book.genero] = genres.get(book.genero, 0) + 1
            if book.autor:
                authors[book.autor] = authors.get(book.autor, 0) + 1
            if book.categoria:
                categories[book.categoria] = categories.get(book.categoria, 0) + 1

        # Calcula pesos baseados nos padrões do usuário
        if genres:
            top_genre_count = max(genres.values())
            genre_focus = top_genre_count / sum(genres.values())
            weights['genero'] *= (1 + genre_focus)

        if authors:
            top_author_count = max(authors.values())
            author_focus = top_author_count / sum(authors.values())
            weights['autor'] *= (1 + author_focus)

        if categories:
            top_category_count = max(categories.values())
            category_focus = top_category_count / sum(categories.values())
            weights['categoria'] *= (1 + category_focus)

        return weights

    def _analyze_user_preferences(self, user: User) -> Dict[str, bool]:
        """
        Analisa preferências do usuário para ajuste de pesos
        """
        shelves = UserBookShelf.objects.filter(
            user=user,
            shelf_type__in=['lido', 'favorito']
        ).select_related('book')

        total_books = shelves.count()
        if total_books < 3:
            return {}

        # Análise de autores
        author_counts = {}
        genre_counts = {}
        publisher_counts = {}

        for shelf in shelves:
            book = shelf.book
            author_counts[book.autor] = author_counts.get(book.autor, 0) + 1
            if book.genero:
                genre_counts[book.genero] = genre_counts.get(book.genero, 0) + 1
            if book.editora:
                publisher_counts[book.editora] = publisher_counts.get(book.editora, 0) + 1

        return {
            'author_loyal': max(author_counts.values(), default=0) / total_books > 0.3,
            'genre_focused': max(genre_counts.values(), default=0) / total_books > 0.4,
            'publisher_focused': max(publisher_counts.values(), default=0) / total_books > 0.25
        }

    def _find_similar_books(self, base_books, weights: Dict[str, float]):
        """
        Encontra livros similares usando critérios ponderados específicos do usuário
        """
        if not base_books.exists():
            return Book.objects.none()

        # Obtém gêneros e autores base
        base_genres = {book.book.genero for book in base_books if book.book.genero}
        base_authors = {book.book.autor for book in base_books if book.book.autor}
        base_categories = {book.book.categoria for book in base_books if book.book.categoria}

        # Constrói query baseada nos padrões do usuário
        query = Q()

        if base_genres:
            query |= Q(genero__in=base_genres)
        if base_authors:
            query |= Q(autor__in=base_authors)
        if base_categories:
            query |= Q(categoria__in=base_categories)

        # Remove livros base
        base_book_ids = [shelf.book.id for shelf in base_books]

        # Aplica filtros e scoring
        similar_books = Book.objects.exclude(
            id__in=base_book_ids
        ).filter(query).annotate(
            similarity_score=Case(
                *[
                     When(genero=genre, then=Value(weights['genero']))
                     for genre in base_genres
                 ] +
                 [
                     When(autor=author, then=Value(weights['autor']))
                     for author in base_authors
                 ] +
                 [
                     When(categoria=category, then=Value(weights['categoria']))
                     for category in base_categories
                 ],
                default=Value(0.0),
                output_field=FloatField()
            )
        ).order_by('-similarity_score')

        return similar_books

    def _combine_recommendations(
            self,
            user: User,
            history_books: list,
            category_books: list,
            similarity_books: list,
            temporal_books: list,
            excluded_books: List[int],
            favorite_books: QuerySet,
            limit: int
    ) -> QuerySet[Book]:
        """
        Combina recomendações com pesos e aleatoriedade
        """
        # Converte excluídos e favoritos para sets para operações mais eficientes
        excluded_set = set(excluded_books)
        favorite_set = set(fb.book.id for fb in favorite_books)

        # Garante que não temos livros excluídos ou favoritos em nenhuma lista
        def filter_books(books):
            return [b for b in books if b.id not in excluded_set and b.id not in favorite_set]

        # Filtra cada lista de recomendações
        history_filtered = filter_books(history_books)
        category_filtered = filter_books(category_books)
        similarity_filtered = filter_books(similarity_books)
        temporal_filtered = filter_books(temporal_books)

        print(f"\nListas filtradas:")
        print(f"History filtrada: {[b.id for b in history_filtered]}")
        print(f"Category filtrada: {[b.id for b in category_filtered]}")
        print(f"Similarity filtrada: {[b.id for b in similarity_filtered]}")
        print(f"Temporal filtrada: {[b.id for b in temporal_filtered]}")

        # Combina todas as recomendações em um único conjunto
        all_recommendations = set()

        # Adiciona recomendações de cada provider mantendo a proporção dos pesos
        for books in [
            (history_filtered, 7),  # 35%
            (category_filtered, 5),  # 25%
            (similarity_filtered, 6),  # 30%
            (temporal_filtered, 2)  # 10%
        ]:
            book_list, slots = books
            if book_list:
                # Pega uma amostra aleatória baseada no peso
                sample_size = min(slots, len(book_list))
                selected = set(random.sample(book_list, sample_size))
                all_recommendations.update(selected)

        # Converte para lista e embaralha
        final_recommendations = list(all_recommendations)
        random.shuffle(final_recommendations)

        # Pega apenas os IDs necessários
        recommended_ids = [book.id for book in final_recommendations[:limit]]

        print(f"\nRecomendações finais após filtragem: {recommended_ids}")

        # Cria o queryset preservando a ordem
        preserved_order = Case(
            *[When(id=id, then=pos) for pos, id in enumerate(recommended_ids)],
            output_field=IntegerField()
        )

        return Book.objects.filter(
            id__in=recommended_ids
        ).order_by(preserved_order)

    def calculate_similarity_score(self, book1, book2):
        """
        Calcula score de similaridade entre dois livros

        Args:
            book1: Primeiro livro
            book2: Segundo livro

        Returns:
            Float com score de similaridade (0.0 a 1.0)
        """
        weights = self.WEIGHTS
        score = 0.0

        # Compara gênero
        if book1.genero and book2.genero and book1.genero == book2.genero:
            score += weights['genero']

        # Compara autor
        if book1.autor and book2.autor and book1.autor == book2.autor:
            score += weights['autor']

        # Compara categoria
        if book1.categoria and book2.categoria and book1.categoria == book2.categoria:
            score += weights['categoria']

        # Compara temas (se ambos tiverem)
        if book1.temas and book2.temas:
            temas1 = set(t.strip().lower() for t in book1.temas.split(','))
            temas2 = set(t.strip().lower() for t in book2.temas.split(','))

            if temas1 and temas2:
                common_temas = temas1.intersection(temas2)
                if common_temas:
                    score += weights['temas'] * (len(common_temas) / max(len(temas1), len(temas2)))

        return score
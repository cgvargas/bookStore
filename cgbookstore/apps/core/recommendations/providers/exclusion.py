from typing import List, Dict
from django.db.models import QuerySet, Q, Count
from django.contrib.auth import get_user_model
from ...models import Book, UserBookShelf

User = get_user_model()


class ExclusionProvider:
    """Provider responsável por gerenciar exclusões de livros nas recomendações"""

    @staticmethod
    def get_excluded_books(user: User) -> List[int]:
        """
        Obtém lista de IDs de livros que devem ser excluídos das recomendações

        Args:
            user: Usuário alvo

        Returns:
            Lista de IDs de livros que não devem ser recomendados
        """
        # Retorna apenas os IDs dos livros excluídos
        return list(UserBookShelf.objects.filter(
            user=user
        ).values_list('book_id', flat=True).distinct())

    @staticmethod
    def _get_user_preferences(user: User) -> Dict:
        """
        Obtém as preferências do usuário baseadas em suas prateleiras
        """
        preferences = {
            'generos': {},
            'categorias': {}
        }

        user_shelves = UserBookShelf.objects.filter(
            user=user
        ).select_related('book')

        for shelf in user_shelves:
            # Peso baseado no tipo de prateleira
            weight = {
                'favorito': 3.0,
                'lido': 1.5,
                'lendo': 1.0,
                'vou_ler': 0.5,
                'abandonei': 0.2
            }.get(shelf.shelf_type, 0.5)

            # Processa gêneros
            if shelf.book.genero:
                for genero in shelf.book.genero.split(','):
                    genero = genero.strip().lower()
                    preferences['generos'][genero] = preferences['generos'].get(genero, 0) + weight

            # Processa categorias
            if shelf.book.categoria:
                categoria = shelf.book.categoria.replace("'", "").replace("[", "").replace("]", "").strip()
                if categoria:
                    preferences['categorias'][categoria.lower()] = preferences['categorias'].get(categoria.lower(),
                                                                                                 0) + weight

        return preferences

    @staticmethod
    def apply_exclusions(queryset: QuerySet, user: User) -> QuerySet:
        """Aplica exclusões e filtragem por preferências"""
        # Remove livros da estante
        excluded_ids = ExclusionProvider.get_excluded_books(user)
        filtered_qs = queryset.exclude(id__in=excluded_ids)

        # Obtém preferências e aplica filtros se houver
        preferences = ExclusionProvider._get_user_preferences(user)

        if preferences['generos'] or preferences['categorias']:
            category_filters = Q()
            genre_filters = Q()

            # Filtra por categorias preferidas
            for categoria, peso in preferences['categorias'].items():
                if peso > 1.0:  # Só considera categorias com peso relevante
                    category_filters |= Q(categoria__icontains=categoria)

            # Filtra por gêneros preferidos
            for genero, peso in preferences['generos'].items():
                if peso > 1.0:  # Só considera gêneros com peso relevante
                    genre_filters |= Q(genero__icontains=genero)

            # Combina filtros
            if category_filters or genre_filters:
                filtered_qs = filtered_qs.filter(category_filters | genre_filters)

        return filtered_qs

    @staticmethod
    def get_available_recommendations(recommendations: dict, user: User) -> dict:
        """Filtra e prioriza recomendações baseado no perfil"""
        excluded_ids = ExclusionProvider.get_excluded_books(user)
        preferences = ExclusionProvider._get_user_preferences(user)

        filtered_recommendations = {}
        for key, queryset in recommendations.items():
            # Aplica exclusões básicas
            filtered_qs = queryset.exclude(id__in=excluded_ids)

            # Ordena por relevância se houver preferências
            if preferences['generos'] or preferences['categorias']:
                filtered_qs = ExclusionProvider._order_by_relevance(filtered_qs, preferences)

            filtered_recommendations[key] = filtered_qs

        return filtered_recommendations

    @staticmethod
    def verify_exclusions(recommended_books: List[Book], user: User) -> List[Book]:
        """Verificação final com priorização por relevância"""
        excluded_ids = ExclusionProvider.get_excluded_books(user)
        preferences = ExclusionProvider._get_user_preferences(user)

        # Remove livros da estante
        available_books = [
            book for book in recommended_books
            if book.id not in excluded_ids
        ]

        # Se houver preferências, prioriza livros relevantes
        if preferences['generos'] or preferences['categorias']:
            scored_books = []
            for book in available_books:
                score = 0

                # Pontua por categoria
                if book.categoria:
                    categoria = book.categoria.lower()
                    score += preferences['categorias'].get(categoria, 0)

                # Pontua por gênero
                if book.genero:
                    for genero in book.genero.split(','):
                        genero = genero.strip().lower()
                        score += preferences['generos'].get(genero, 0)

                scored_books.append((book, score))

            # Ordena por score e preserva alguma diversidade
            scored_books.sort(key=lambda x: (-x[1], x[0].titulo))
            return [book for book, _ in scored_books]

        return available_books

    @staticmethod
    def _order_by_relevance(queryset: QuerySet, preferences: Dict) -> QuerySet:
        """Ordena queryset por relevância baseada nas preferências"""
        for categoria, peso in preferences['categorias'].items():
            if peso > 1.0:
                queryset = queryset.annotate(
                    relevance_categoria=Count('categoria', filter=Q(categoria__icontains=categoria))
                )

        for genero, peso in preferences['generos'].items():
            if peso > 1.0:
                queryset = queryset.annotate(
                    relevance_genero=Count('genero', filter=Q(genero__icontains=genero))
                )

        return queryset.order_by('-relevance_categoria', '-relevance_genero', 'titulo')
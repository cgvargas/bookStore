from django.db.models import Count, Q
from ...models import Book, User, UserBookShelf
from ..utils.processors import CategoryProcessor


class CategoryBasedProvider:
    """Provider de recomendações baseadas em categorias"""

    def __init__(self):
        self._processor = CategoryProcessor()

    def get_recommendations(self, user: User, limit: int = 20):
        """
        Gera recomendações baseadas nas categorias preferidas
        Args:
            user: Usuário alvo
            limit: Limite de recomendações
        Returns:
            QuerySet com livros recomendados
        """
        # Obtém categorias preferidas
        user_preferences = self._get_user_preferences(user)

        # Filtra livros baseados nas preferências
        recommendations = Book.objects.filter(
            Q(genero__in=user_preferences['genres']) |
            Q(categoria__in=user_preferences['categories'])
        ).exclude(
            id__in=self._get_read_books(user)
        ).order_by('?')[:limit]

        return recommendations

    def _get_user_preferences(self, user: User) -> dict:
        """
        Analisa preferências do usuário baseado em seu histórico
        Args:
            user: Usuário alvo
        Returns:
            Dicionário com preferências
        """
        read_books = UserBookShelf.objects.filter(
            user=user,
            shelf_type='lido'
        ).select_related('book')

        # Processa dados para extrair preferências
        return self._processor.extract_preferences(read_books)

    def _get_read_books(self, user: User):
        """
        Obtém IDs dos livros já lidos pelo usuário
        Args:
            user: Usuário alvo
        Returns:
            Lista de IDs
        """
        return UserBookShelf.objects.filter(
            user=user
        ).values_list('book', flat=True)

    def get_category_affinity(self, user: User) -> dict:
        """
        Calcula afinidade do usuário com diferentes categorias
        Args:
            user: Usuário alvo
        Returns:
            Dicionário com scores por categoria
        """
        read_books = UserBookShelf.objects.filter(
            user=user,
            shelf_type='lido'
        ).select_related('book')

        genres = {}
        categories = {}
        themes = {}

        for shelf in read_books:
            # Contagem de gêneros
            genre = shelf.book.genero
            if genre:
                genres[genre] = genres.get(genre, 0) + 1

            # Contagem de categorias
            category = shelf.book.categoria
            if category:
                categories[category] = categories.get(category, 0) + 1

            # Contagem de temas
            if shelf.book.temas:
                for tema in shelf.book.temas.split(','):
                    tema = tema.strip()
                    if tema:
                        themes[tema] = themes.get(tema, 0) + 1

        return {
            'genres': genres,
            'categories': categories,
            'themes': themes
        }
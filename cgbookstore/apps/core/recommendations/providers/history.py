from django.db.models import Count, Q
from ...models import Book, User, UserBookShelf


class HistoryBasedProvider:
    """Provider de recomendações baseadas no histórico do usuário"""

    def get_recommendations(self, user: User, limit: int = 20):
        """
        Gera recomendações baseadas no histórico de leitura
        Args:
            user: Usuário alvo
            limit: Limite de recomendações
        Returns:
            QuerySet com livros recomendados
        """
        # Obtém livros já lidos pelo usuário
        read_books = UserBookShelf.objects.filter(
            user=user,
            shelf_type='lido'
        ).values_list('book', flat=True)

        # Se não houver histórico, retorna livros aleatórios
        if not read_books:
            return Book.objects.all().order_by('?')[:limit]

        # Obtém autores mais lidos
        favorite_authors = Book.objects.filter(
            id__in=read_books
        ).values('autor').annotate(
            count=Count('autor')
        ).order_by('-count').values_list('autor', flat=True)

        # Obtém gêneros mais lidos
        favorite_genres = Book.objects.filter(
            id__in=read_books
        ).values('genero').annotate(
            count=Count('genero')
        ).order_by('-count').values_list('genero', flat=True)

        # Recomenda livros similares excluindo os já lidos
        recommendations = Book.objects.filter(
            Q(autor__in=favorite_authors[:3]) |
            Q(genero__in=favorite_genres[:3])
        ).exclude(
            id__in=read_books
        ).distinct().order_by('?')[:limit]

        return recommendations

    def get_reading_patterns(self, user: User) -> dict:
        """
        Analisa padrões de leitura do usuário
        Args:
            user: Usuário alvo
        Returns:
            Dicionário com estatísticas de leitura
        """
        read_books = UserBookShelf.objects.filter(
            user=user,
            shelf_type='lido'
        ).select_related('book')

        patterns = {
            'total_books': 0,
            'favorite_authors': {},
            'favorite_genres': {},
            'reading_frequency': {}
        }

        for shelf in read_books:
            patterns['total_books'] += 1

            # Contagem de autores
            author = shelf.book.autor
            patterns['favorite_authors'][author] = \
                patterns['favorite_authors'].get(author, 0) + 1

            # Contagem de gêneros
            genre = shelf.book.genero
            if genre:
                patterns['favorite_genres'][genre] = \
                    patterns['favorite_genres'].get(genre, 0) + 1

            # Análise temporal
            month = shelf.added_at.strftime('%Y-%m')
            patterns['reading_frequency'][month] = \
                patterns['reading_frequency'].get(month, 0) + 1

        return patterns
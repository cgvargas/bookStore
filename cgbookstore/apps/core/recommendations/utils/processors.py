from collections import Counter
from typing import List, Dict, Set
from django.db.models import QuerySet
from ...models import Book


class BaseProcessor:
    """Classe base para processadores"""

    def _get_most_common(self, items: List, limit: int) -> List:
        """
        Obtém os items mais comuns da lista
        Args:
            items: Lista de items
            limit: Limite de items
        Returns:
            Lista com os mais comuns
        """
        return [item for item, _ in Counter(items).most_common(limit)]


class CategoryProcessor(BaseProcessor):
    """Processador para análise de categorias e preferências"""

    def extract_preferences(self, read_books: QuerySet) -> Dict:
        """
        Extrai preferências do usuário baseado nos livros lidos
        Args:
            read_books: QuerySet com livros lidos
        Returns:
            Dicionário com preferências
        """
        genres = []
        categories = []
        themes = []

        for shelf in read_books:
            book = shelf.book

            if book.genero:
                genres.append(book.genero)
            if book.categoria:
                categories.append(book.categoria)
            if book.temas:
                themes.extend([tema.strip() for tema in book.temas.split(',')])

        # Obtém os mais frequentes
        return {
            'genres': self._get_most_common(genres, 5),
            'categories': self._get_most_common(categories, 5),
            'themes': self._get_most_common(themes, 10)
        }


class SimilarityProcessor(BaseProcessor):
    """Processador para cálculo de similaridade entre livros"""

    # Pesos para diferentes aspectos
    WEIGHTS = {
        'autor': 0.40,
        'genero': 0.35,
        'categoria': 0.15,
        'temas': 0.07,
        'data_publicacao': 0.03
    }

    def calculate_similarity(self, book1: Book, book2: Book) -> float:
        """
        Calcula similaridade entre dois livros
        Args:
            book1: Primeiro livro
            book2: Segundo livro
        Returns:
            Score de similaridade (0-1)
        """
        scores = []

        # Autor
        if book1.autor == book2.autor:
            scores.append(('autor', 1.0))

        # Gênero
        if book1.genero == book2.genero:
            scores.append(('genero', 1.0))

        # Categoria
        if book1.categoria and book2.categoria:
            if book1.categoria == book2.categoria:
                scores.append(('categoria', 1.0))

        # Temas
        if book1.temas and book2.temas:
            temas1 = set(t.strip() for t in book1.temas.split(','))
            temas2 = set(t.strip() for t in book2.temas.split(','))
            common_temas = temas1 & temas2
            all_temas = temas1 | temas2
            if all_temas:
                tema_score = len(common_temas) / len(all_temas)
                scores.append(('temas', tema_score))

        # Data de Publicação
        if book1.data_publicacao and book2.data_publicacao:
            year_diff = abs(book1.data_publicacao.year - book2.data_publicacao.year)
            year_score = max(0, 1 - (year_diff / 100))  # Diferença máxima de 100 anos
            scores.append(('data_publicacao', year_score))

            # Calcula score final ponderado
            if not scores:
                return 0.0

            # Penaliza a falta de matches em aspectos importantes
            base_score = sum(self.WEIGHTS[aspect] * score for aspect, score in scores)

            # Se autor ou gênero são diferentes, reduz o score
            if not any(aspect == 'autor' for aspect, _ in scores):
                base_score *= 0.5
            if not any(aspect == 'genero' for aspect, _ in scores):
                base_score *= 0.6

            return base_score

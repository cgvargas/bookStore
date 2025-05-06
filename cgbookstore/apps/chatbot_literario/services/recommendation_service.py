import logging
from django.contrib.auth import get_user_model
from django.db.models import Count, Q

# Importar as funcionalidades do sistema de recomendação existente
try:
    from cgbookstore.apps.core.recommendations.engine import RecommendationEngine
    from cgbookstore.apps.core.models.book import Book

    RECOMMENDATION_AVAILABLE = True
except ImportError:
    RECOMMENDATION_AVAILABLE = False
    logging.warning("Sistema de recomendação não disponível para o chatbot")

logger = logging.getLogger(__name__)


class ChatbotRecommendationService:
    """
    Serviço que integra o chatbot com o sistema de recomendações existente.
    """

    def __init__(self):
        self.engine = None
        if RECOMMENDATION_AVAILABLE:
            try:
                self.engine = RecommendationEngine()
                logger.info("Engine de recomendação inicializado com sucesso para o chatbot")
            except Exception as e:
                logger.error(f"Erro ao inicializar engine de recomendação para chatbot: {str(e)}")

    def get_recommendations_by_genre(self, genre, limit=5):
        """Obtém recomendações por gênero literário."""
        try:
            if not RECOMMENDATION_AVAILABLE or not self.engine:
                return self._fallback_recommendations_by_genre(genre, limit)

            # Utilizar a engine de recomendação existente
            recommendations = self.engine.get_recommendations_by_category(genre, limit=limit)
            return recommendations

        except Exception as e:
            logger.error(f"Erro ao obter recomendações por gênero: {str(e)}")
            return self._fallback_recommendations_by_genre(genre, limit)

    def get_personalized_recommendations(self, user, limit=5):
        """Obtém recomendações personalizadas para o usuário."""
        try:
            if not RECOMMENDATION_AVAILABLE or not self.engine:
                return self._fallback_personalized_recommendations(user, limit)

            # Utilizar a engine de recomendação existente
            recommendations = self.engine.get_personalized_recommendations(user, limit=limit)
            return recommendations

        except Exception as e:
            logger.error(f"Erro ao obter recomendações personalizadas: {str(e)}")
            return self._fallback_personalized_recommendations(user, limit)

    def _fallback_recommendations_by_genre(self, genre, limit=5):
        """Sistema de fallback quando o engine de recomendação não está disponível."""
        try:
            return Book.objects.filter(
                Q(categoria__icontains=genre) |
                Q(tags__icontains=genre)
            ).order_by('-data_publicacao')[:limit]
        except Exception:
            return []

    def _fallback_personalized_recommendations(self, user, limit=5):
        """Sistema de fallback para recomendações personalizadas."""
        try:
            # Obter as categorias mais lidas pelo usuário
            favorite_categories = user.userbookshelf_set.values('book__categoria').annotate(
                count=Count('book__categoria')
            ).order_by('-count')[:3]

            category_list = [item['book__categoria'] for item in favorite_categories if item['book__categoria']]

            if not category_list:
                # Se não houver categorias favoritas, retornar livros populares
                return Book.objects.all().order_by('-popularidade')[:limit]

            # Filtrar livros por categorias favoritas que o usuário ainda não adicionou
            user_books = user.userbookshelf_set.values_list('book_id', flat=True)
            recommendations = Book.objects.filter(
                categoria__in=category_list
            ).exclude(
                id__in=user_books
            ).order_by('-popularidade')[:limit]

            return recommendations
        except Exception as e:
            logger.error(f"Erro no fallback de recomendações: {str(e)}")
            return []

    def format_book_recommendations(self, books):
        """Formata uma lista de livros para apresentação no chatbot."""
        if not books:
            return "Não encontrei recomendações que correspondam aos critérios."

        result = "Aqui estão algumas recomendações:\n\n"
        for i, book in enumerate(books, 1):
            result += f"{i}. {book.titulo} - {book.autor}\n"
            if book.categoria:
                result += f"   Gênero: {book.categoria}\n"
            if hasattr(book, 'descricao') and book.descricao:
                # Limitar a descrição a 100 caracteres
                desc = book.descricao[:100] + "..." if len(book.descricao) > 100 else book.descricao
                result += f"   Sinopse: {desc}\n"
            result += "\n"

        return result


# Instância para uso no aplicativo
recommendation_service = ChatbotRecommendationService()
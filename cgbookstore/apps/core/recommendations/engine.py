from typing import List, Set, Dict, Any, Union
from django.core.cache import caches
from django.contrib.auth import get_user_model

from .providers.history import HistoryBasedProvider
from .providers.category import CategoryBasedProvider
from .providers.similarity import SimilarityBasedProvider
from .providers.exclusion import ExclusionProvider
from .providers.temporal import TemporalProvider
from .providers.external_api import ExternalApiProvider
from .services.calculator import RecommendationCalculator
from ..models import Book, UserBookShelf

import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class RecommendationEngine:
    """Motor de recomendações que prioriza recomendações externas"""

    def __init__(self):
        self._cache = caches['recommendations']
        self._external_provider = ExternalApiProvider()
        self._history_provider = HistoryBasedProvider()
        self._category_provider = CategoryBasedProvider()
        self._similarity_provider = SimilarityBasedProvider()
        self._temporal_provider = TemporalProvider()
        self._exclusion_provider = ExclusionProvider()
        self._calculator = RecommendationCalculator()
        self.DEFAULT_LIMIT = 20
        self.MIN_RECOMMENDATIONS = 10

    def get_recommendations(self, user: User, limit: int = None) -> List[Union[Book, Dict]]:
        """Obtém recomendações priorizando resultados externos"""
        if limit is None:
            limit = self.DEFAULT_LIMIT

        try:
            logger.info("\n=== Iniciando recomendações com prioridade externa ===")

            # 1. Primeiro, busca recomendações externas
            logger.info("Buscando recomendações externas...")
            external_books = self._external_provider.get_recommendations(
                user=user,
                limit=limit
            )
            logger.info(f"Recomendações externas encontradas: {len(external_books)}")

            # 2. Se não houver suficientes, complementa com locais
            needed = limit - len(external_books)
            local_books = []

            if needed > 0:
                logger.info(f"\nComplementando com {needed} recomendações locais")
                excluded_books = self._exclusion_provider.get_excluded_books(user)
                local_books = self._get_local_recommendations(user, excluded_books, needed)
                logger.info(f"Recomendações locais complementares: {len(local_books)}")

            # Combina os resultados
            all_recommendations = external_books + local_books
            logger.info(f"\nTotal de recomendações: {len(all_recommendations)}")
            logger.info(f"- Externas: {len(external_books)}")
            logger.info(f"- Locais: {len(local_books)}")

            # Armazena os resultados no cache
            cache_key = self._get_cache_key(user)

            # Processamento uniforme para o cache
            external_ids = []
            for book in external_books:
                if isinstance(book, dict):
                    # Formato Google Books API
                    book_id = book.get('id')
                    if book_id:
                        external_ids.append(book_id)
                else:
                    # Objeto Book temporário
                    if hasattr(book, 'external_id') and book.external_id:
                        external_ids.append(book.external_id)
                    elif hasattr(book, 'id'):
                        external_ids.append(f"temp_{book.id}")

            # Filtra livros locais válidos (não temporários)
            local_ids = [
                book.id for book in local_books
                if not getattr(book, 'is_temporary', False) and book.id
            ]

            cache_data = {
                'external': external_ids,
                'local': local_ids,
                'has_external': bool(external_ids),
                'total': len(all_recommendations)
            }
            self._cache.set(cache_key, cache_data)

            return all_recommendations

        except Exception as e:
            import traceback
            logger.error(f"Erro ao gerar recomendações: {str(e)}")
            logger.error(traceback.format_exc())
            return self._get_fallback_recommendations(user, [], limit)

    def get_mixed_recommendations(self, user: User, limit: int = 20) -> Dict[str, Any]:
        """Obtém recomendações mistas, priorizando externas"""
        try:
            # Obtém todas as recomendações
            recommendations = self.get_recommendations(user, limit)

            # Separa recomendações por tipo
            external_books = []
            local_books = []

            for book in recommendations:
                try:
                    # Verifica tipo e atributos do livro para classificação correta
                    if isinstance(book, dict):
                        # É um dicionário (formato da API do Google Books)
                        external_books.append(book)
                    elif hasattr(book, 'is_temporary') and book.is_temporary:
                        # É um objeto Book temporário (do ExternalApiProvider)
                        external_books.append(book)
                    elif hasattr(book, 'external_id') and book.external_id:
                        # Tem ID externo, tratamos como externo
                        external_books.append(book)
                    else:
                        # Caso contrário, é um livro local do banco de dados
                        local_books.append(book)
                except Exception as book_error:
                    logger.error(f"Erro ao processar livro individual: {str(book_error)}")
                    # Pula este livro para não interromper todo o processo
                    continue

            logger.info(f"\nTotal de recomendações mistas:")
            logger.info(f"- Externas: {len(external_books)}")
            logger.info(f"- Locais: {len(local_books)}")

            return {
                'local': local_books,
                'external': external_books,
                'has_external': bool(external_books),
                'total': len(recommendations)
            }

        except Exception as e:
            logger.error(f"Erro ao obter recomendações mistas: {str(e)}")
            return {
                'local': [],
                'external': [],
                'has_external': False,
                'total': 0
            }

    def get_personalized_shelf(self, user: User, shelf_size: int = 20) -> Dict[str, Any]:
        """Gera uma prateleira personalizada priorizando conteúdo externo"""
        try:
            # Obtém recomendações mistas (priorizando externas)
            mixed_data = self.get_mixed_recommendations(user, limit=shelf_size)
            external_books = mixed_data.get('external', [])
            local_books = mixed_data.get('local', [])

            # Organiza livros por categoria
            by_category = {}
            for book in local_books:
                if not hasattr(book, 'categoria') or not book.categoria:
                    continue

                # Extrair categoria principal com tratamento seguro
                try:
                    if book.categoria.startswith('[') and book.categoria.endswith(']'):
                        # Formato lista em string
                        categories = book.categoria.strip("[]'").split(',')
                        if categories:
                            category = categories[0].strip()
                        else:
                            continue
                    else:
                        # Formato string simples
                        category = book.categoria.split(',')[0].strip()

                    if not category:
                        continue

                    if category not in by_category:
                        by_category[category] = []
                    if len(by_category[category]) < 5:
                        by_category[category].append(book)
                except (AttributeError, IndexError, ValueError) as e:
                    logger.warning(f"Erro ao processar categoria do livro: {str(e)}")
                    continue

            # Organiza por autor
            by_author = {}
            for book in local_books:
                if not hasattr(book, 'autor') or not book.autor:
                    continue

                try:
                    author = book.autor.split(',')[0].strip()
                    if not author:
                        continue

                    if author not in by_author:
                        by_author[author] = []
                    if len(by_author[author]) < 3:
                        by_author[author].append(book)
                except (AttributeError, IndexError) as e:
                    logger.warning(f"Erro ao processar autor do livro: {str(e)}")
                    continue

            # Destaques (priorizando externos)
            highlights = []

            # Primeiro adiciona destaques externos
            for book in external_books[:3]:
                if len(highlights) < 5:
                    highlights.append(book)

            # Complementa com destaques locais
            for book in local_books:
                if len(highlights) >= 5:
                    break

                try:
                    # Verifica se é destaque por algum critério
                    is_highlight = (
                            getattr(book, 'e_destaque', False) or
                            getattr(book, 'quantidade_vendida', 0) > 0 or
                            getattr(book, 'quantidade_acessos', 0) > 0
                    )

                    if is_highlight:
                        highlights.append(book)
                except Exception as e:
                    logger.warning(f"Erro ao verificar destaque do livro: {str(e)}")
                    continue

            # Filtra seções com conteúdo suficiente
            filtered_categories = {k: v for k, v in by_category.items() if len(v) > 1}
            filtered_authors = {k: v for k, v in by_author.items() if len(v) > 1}

            return {
                'destaques': highlights,
                'por_genero': filtered_categories,
                'por_autor': filtered_authors,
                'external_books': external_books,
                'has_external': bool(external_books),
                'total': len(external_books) + len(local_books)
            }

        except Exception as e:
            logger.error(f"Erro ao gerar prateleira personalizada: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

            # Retorna estrutura vazia mas válida em caso de erro
            return {
                'destaques': [],
                'por_genero': {},
                'por_autor': {},
                'external_books': [],
                'has_external': False,
                'total': 0
            }

    def _get_local_recommendations(self, user: User, excluded_books: Set[int], limit: int) -> List[Book]:
        """Obtém recomendações locais complementares"""
        try:
            # Provedores de recomendações
            providers = [
                self._history_provider,
                self._category_provider,
                self._similarity_provider,
                self._temporal_provider
            ]

            local_books = []
            provider_weights = {
                HistoryBasedProvider: 0.35,
                CategoryBasedProvider: 0.25,
                SimilarityBasedProvider: 0.30,
                TemporalProvider: 0.10
            }

            for provider in providers:
                try:
                    # Calcula quantidade de livros para cada provedor
                    provider_limit = max(1, int(limit * provider_weights.get(type(provider), 0.2)))

                    # Obtém recomendações do provedor
                    provider_recommendations = provider.get_recommendations(
                        user=user,
                        limit=provider_limit
                    )

                    # Filtra livros já recomendados e excluídos
                    provider_recommendations = [
                        book for book in provider_recommendations
                        if book.id not in excluded_books and
                           book.id not in [b.id for b in local_books]
                    ]

                    local_books.extend(provider_recommendations)

                    # Para quando atingir o limite
                    if len(local_books) >= limit:
                        break

                except Exception as inner_e:
                    logger.error(f"Erro no provedor {type(provider).__name__}: {str(inner_e)}")
                    continue

            # Garantir limite máximo de livros
            local_books = local_books[:limit]

            # Se não houver livros suficientes, busca genéricos
            if not local_books:
                local_books = list(Book.objects.exclude(
                    id__in=excluded_books
                ).order_by('?')[:limit])

            return local_books

        except Exception as e:
            logger.error(f"Erro crítico em _get_local_recommendations: {str(e)}")
            # Fallback para recomendações genéricas
            return list(Book.objects.exclude(
                id__in=excluded_books
            ).order_by('?')[:limit])

    def _get_cache_key(self, user: User) -> str:
        """Gera chave de cache única para o usuário"""
        try:
            shelf_books = self._get_user_shelf_books(user)
            shelf_hash = hash(tuple(sorted(shelf_books)))
            shelf_count = len(shelf_books)

            cache_key = f'recommendations:{user.id}:{shelf_hash}:{shelf_count}'
            logger.info(f"Cache key gerada: {cache_key}")
            return cache_key
        except Exception as e:
            logger.error(f"Erro ao gerar chave de cache: {str(e)}")
            # Fallback para chave simples
            return f'recommendations:{user.id}:fallback'

    def _get_user_shelf_books(self, user: User) -> List[int]:
        """Obtém IDs dos livros nas prateleiras do usuário"""
        try:
            return list(UserBookShelf.objects.filter(
                user=user
            ).values_list('book_id', flat=True))
        except Exception as e:
            logger.error(f"Erro ao obter livros da prateleira: {str(e)}")
            return []

    def _get_fallback_recommendations(self, user: User, excluded_books: List[int], limit: int) -> List[Book]:
        """Recomendações de fallback quando ocorrem erros"""
        logger.warning("Usando recomendações de fallback")
        try:
            return list(Book.objects.exclude(
                id__in=excluded_books
            ).order_by('?')[:limit])
        except Exception as e:
            logger.error(f"Erro em recomendações fallback: {str(e)}")
            return []
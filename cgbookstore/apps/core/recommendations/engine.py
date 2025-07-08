# cgbookstore/apps/core/recommendations/engine.py

from typing import List, Set, Dict, Any, Union
from django.core.cache import caches
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

from .providers.history import HistoryBasedProvider
from .providers.category import CategoryBasedProvider
from .providers.similarity import SimilarityBasedProvider
from .providers.exclusion import ExclusionProvider
from .providers.temporal import TemporalProvider
from .providers.external_api import ExternalApiProvider
from .providers.language_preference import LanguagePreferenceProvider
from .services.calculator import RecommendationCalculator
from ..models import Book, UserBookShelf

import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class RecommendationEngine:
    """Motor de recomendações com priorização local e análise de idioma"""

    def __init__(self):
        self._cache = caches['recommendations']

        # Providers locais
        self._history_provider = HistoryBasedProvider()
        self._category_provider = CategoryBasedProvider()
        self._similarity_provider = SimilarityBasedProvider()
        self._temporal_provider = TemporalProvider()
        self._language_provider = LanguagePreferenceProvider()
        self._exclusion_provider = ExclusionProvider()

        # Provider externo (usado apenas quando necessário)
        self._external_provider = ExternalApiProvider()

        self._calculator = RecommendationCalculator()
        self.DEFAULT_LIMIT = 20
        self.MIN_LOCAL_RECOMMENDATIONS = 15  # Aumentado para priorizar local
        self.EXTERNAL_THRESHOLD = 0.3  # Máximo 30% de recomendações externas

    def get_recommendations(self, user: User, limit: int = None) -> List[Union[Book, Dict]]:
        """Obtém recomendações priorizando resultados locais e preferências de idioma"""
        if limit is None:
            limit = self.DEFAULT_LIMIT

        try:
            logger.info("\n=== Iniciando recomendações com prioridade local ===")

            # 1. Primeiro, busca recomendações locais
            excluded_books = self._exclusion_provider.get_excluded_books(user)

            # Obtém perfil de idioma do usuário
            language_profile = self._language_provider.get_language_affinity(user)
            logger.info(f"Perfil de idioma: {language_profile}")

            # Calcula pesos adaptativos baseados no perfil do usuário
            adaptive_weights = self._calculate_adaptive_weights(user, language_profile)
            logger.info(f"Pesos adaptativos: {adaptive_weights}")

            # Obtém recomendações locais com pesos adaptativos
            local_books = self._get_local_recommendations(
                user,
                excluded_books,
                limit,
                adaptive_weights
            )
            local_count = len(local_books)
            logger.info(f"Recomendações locais encontradas: {local_count}")

            # 2. Decide se precisa de recomendações externas
            external_books = []
            max_external = int(limit * self.EXTERNAL_THRESHOLD)

            if local_count < self.MIN_LOCAL_RECOMMENDATIONS and max_external > 0:
                logger.info(f"Buscando até {max_external} recomendações externas complementares")

                # Busca recomendações externas focadas no idioma preferido
                external_books = self._get_filtered_external_recommendations(
                    user,
                    language_profile,
                    min(max_external, limit - local_count)
                )
                logger.info(f"Recomendações externas obtidas: {len(external_books)}")

            # 3. Combina resultados mantendo prioridade local
            all_recommendations = self._merge_recommendations(
                local_books,
                external_books,
                limit
            )

            logger.info(f"\nTotal de recomendações: {len(all_recommendations)}")
            logger.info(f"- Locais: {len([r for r in all_recommendations if not self._is_external(r)])}")
            logger.info(f"- Externas: {len([r for r in all_recommendations if self._is_external(r)])}")

            # Armazena no cache
            self._update_cache(user, all_recommendations)

            return all_recommendations

        except Exception as e:
            import traceback
            logger.error(f"Erro ao gerar recomendações: {str(e)}")
            logger.error(traceback.format_exc())
            return self._get_fallback_recommendations(user, [], limit)

    def _calculate_adaptive_weights(self, user: User, language_profile: Dict) -> Dict:
        """Calcula pesos adaptativos baseados no perfil do usuário"""
        # Pesos base
        base_weights = {
            'history': 0.25,
            'category': 0.20,
            'similarity': 0.25,
            'temporal': 0.10,
            'language': 0.20
        }

        # Analisa padrões do usuário
        user_stats = self._analyze_user_behavior(user)

        # Ajusta pesos baseado no comportamento
        if user_stats['is_eclectic']:
            # Usuário eclético - aumenta peso de categoria e similaridade
            base_weights['category'] += 0.05
            base_weights['similarity'] += 0.05
            base_weights['history'] -= 0.10

        if user_stats['is_loyal_reader']:
            # Leitor fiel a autores/séries - aumenta história e similaridade
            base_weights['history'] += 0.10
            base_weights['similarity'] += 0.05
            base_weights['category'] -= 0.15

        if language_profile['portuguese_preference'] > 0.7:
            # Forte preferência por português - aumenta peso de idioma
            base_weights['language'] += 0.10
            base_weights['temporal'] -= 0.10

        if user_stats['seasonal_reader']:
            # Leitor sazonal - aumenta peso temporal
            base_weights['temporal'] += 0.10
            base_weights['category'] -= 0.10

        # Normaliza pesos para somar 1.0
        total = sum(base_weights.values())
        return {k: v / total for k, v in base_weights.items()}

    def _analyze_user_behavior(self, user: User) -> Dict:
        """Analisa comportamento de leitura do usuário"""
        stats = {
            'is_eclectic': False,
            'is_loyal_reader': False,
            'seasonal_reader': False,
            'avg_books_per_month': 0
        }

        try:
            user_books = UserBookShelf.objects.filter(
                user=user,
                shelf_type__in=['lido', 'lendo', 'favorito']
            ).select_related('book')

            if user_books.count() < 3: # <--- Linha alterada (era 5)
                return stats

            # Verifica ecletismo (variedade de gêneros)
            genres = set()
            authors = {}

            for shelf in user_books:
                if shelf.book.genero:
                    genres.add(shelf.book.genero)
                if shelf.book.autor:
                    authors[shelf.book.autor] = authors.get(shelf.book.autor, 0) + 1

            stats['is_eclectic'] = len(genres) > 5

            # Verifica fidelidade a autores
            if authors:
                max_author_count = max(authors.values())
                stats['is_loyal_reader'] = max_author_count >= 3

            # Verifica padrão sazonal (simplificado)
            from django.utils import timezone # Importação movida para dentro do try para escopo local se necessário
            from datetime import timedelta

            recent_books = user_books.filter(
                added_at__gte=timezone.now() - timedelta(days=365)
            )

            if recent_books.count() >= 12:
                # Agrupa por mês
                books_by_month = {}
                for shelf in recent_books:
                    month = shelf.added_at.month
                    books_by_month[month] = books_by_month.get(month, 0) + 1

                # Verifica variação mensal
                if books_by_month:
                    avg = sum(books_by_month.values()) / 12
                    variance = sum((count - avg) ** 2 for count in books_by_month.values()) / 12
                    stats['seasonal_reader'] = variance > 2.0

        except Exception as e:
            logger.error(f"Erro ao analisar comportamento do usuário: {str(e)}")

        return stats

    def _get_local_recommendations(
            self,
            user: User,
            excluded_books: Set[int],
            limit: int,
            weights: Dict
    ) -> List[Book]:
        """Obtém recomendações locais com pesos adaptativos"""
        try:
            # Providers locais
            providers = [
                (self._history_provider, 'history'),
                (self._category_provider, 'category'),
                (self._similarity_provider, 'similarity'),
                (self._temporal_provider, 'temporal'),
                (self._language_provider, 'language')
            ]

            all_recommendations = []
            recommendations_by_provider = {}

            for provider, name in providers:
                try:
                    # Calcula limite baseado no peso
                    provider_limit = max(1, int(limit * weights.get(name, 0.2) * 1.5))

                    # Obtém recomendações
                    provider_recommendations = provider.get_recommendations(
                        user=user,
                        limit=provider_limit
                    )

                    # Armazena para análise
                    recommendations_by_provider[name] = list(provider_recommendations)

                    logger.info(f"Provider {name}: {len(recommendations_by_provider[name])} recomendações")

                except Exception as e:
                    logger.error(f"Erro no provider {name}: {str(e)}")
                    recommendations_by_provider[name] = []

            # Combina recomendações com deduplicação inteligente
            seen_books = set()

            # Primeira passada: adiciona top recomendações de cada provider
            for provider_name, books in recommendations_by_provider.items():
                weight = weights.get(provider_name, 0.2)
                top_count = max(1, int(len(books) * weight))

                for book in books[:top_count]:
                    if book.id not in seen_books and book.id not in excluded_books:
                        all_recommendations.append(book)
                        seen_books.add(book.id)

            # Segunda passada: preenche com recomendações restantes
            for provider_name, books in recommendations_by_provider.items():
                weight = weights.get(provider_name, 0.2)
                top_count = max(1, int(len(books) * weight))

                for book in books[top_count:]:
                    if len(all_recommendations) >= limit:
                        break
                    if book.id not in seen_books and book.id not in excluded_books:
                        all_recommendations.append(book)
                        seen_books.add(book.id)

            # Ordena por relevância combinada
            all_recommendations = self._sort_by_relevance(all_recommendations, user)

            return all_recommendations[:limit]

        except Exception as e:
            logger.error(f"Erro em _get_local_recommendations: {str(e)}")
            return list(Book.objects.exclude(
                id__in=excluded_books
            ).order_by('-quantidade_acessos', '?')[:limit])

    def _get_filtered_external_recommendations(
            self,
            user: User,
            language_profile: Dict,
            limit: int
    ) -> List[Dict]:
        """Obtém recomendações externas filtradas por idioma"""
        try:
            # Modifica os padrões de busca para incluir idioma
            original_patterns = self._external_provider._get_user_patterns(user)

            # Se usuário prefere português, adiciona filtros de idioma
            if language_profile['portuguese_preference'] > 0.5:
                # Adiciona termos em português aos padrões
                filtered_patterns = []
                for pattern in original_patterns[:3]:  # Limita para não sobrecarregar
                    if not pattern.startswith('inauthor:'):
                        filtered_patterns.append(f'{pattern} portuguese')
                        filtered_patterns.append(f'{pattern} brasil')

                # Adiciona autores brasileiros se houver preferência
                if language_profile['national_authors_preference'] > 2.0:
                    filtered_patterns.extend([
                        'inauthor:"Paulo Coelho"',
                        'inauthor:"Clarice Lispector"',
                        'inauthor:"Jorge Amado"'
                    ])
            else:
                filtered_patterns = original_patterns

            # Temporariamente modifica os padrões do provider
            self._external_provider.max_patterns = len(filtered_patterns)

            # Busca recomendações
            external_books = self._external_provider.get_recommendations(
                user=user,
                limit=limit
            )

            # Restaura configuração original
            self._external_provider.max_patterns = 5

            return external_books

        except Exception as e:
            logger.error(f"Erro ao obter recomendações externas filtradas: {str(e)}")
            return []

    def _merge_recommendations(
            self,
            local_books: List[Book],
            external_books: List[Dict],
            limit: int
    ) -> List[Union[Book, Dict]]:
        """Mescla recomendações mantendo prioridade local"""
        merged = []

        # Adiciona livros locais primeiro
        merged.extend(local_books)

        # Adiciona externos se houver espaço
        remaining_slots = limit - len(merged)
        if remaining_slots > 0 and external_books:
            merged.extend(external_books[:remaining_slots])

        return merged[:limit]

    def _sort_by_relevance(self, books: List[Book], user: User) -> List[Book]:
        """Ordena livros por relevância combinada"""
        try:
            # Obtém preferências do usuário
            language_profile = self._language_provider.get_language_affinity(user)

            scored_books = []
            for book in books:
                score = 0.0

                # Pontuação por popularidade
                score += book.quantidade_acessos * 0.001
                score += book.quantidade_vendida * 0.01

                # Boost para livros em destaque
                if book.e_destaque:
                    score *= 1.5

                # Boost para idioma preferido
                if book.idioma and language_profile['portuguese_preference'] > 0.5:
                    if self._language_provider._is_portuguese(book.idioma):
                        score *= 1.3

                # Penalidade para idiomas evitados
                if book.idioma:
                    normalized_lang = self._language_provider._normalize_language(book.idioma)
                    if normalized_lang in language_profile.get('avoided_languages', {}):
                        score *= 0.5

                scored_books.append((book, score))

            # Ordena por score
            scored_books.sort(key=lambda x: x[1], reverse=True)

            # Retorna livros ordenados
            return [book for book, _ in scored_books]

        except Exception as e:
            logger.error(f"Erro ao ordenar por relevância: {str(e)}")
            return books

    def _is_external(self, book: Union[Book, Dict]) -> bool:
        """Verifica se é uma recomendação externa"""
        if isinstance(book, dict):
            return True
        return hasattr(book, 'is_temporary') and book.is_temporary

    def _update_cache(self, user: User, recommendations: List) -> None:
        """Atualiza cache com nova estrutura"""
        try:
            cache_key = self._get_cache_key(user)

            # Separa recomendações por tipo
            local_ids = []
            external_ids = []

            for book in recommendations:
                if self._is_external(book):
                    if isinstance(book, dict):
                        external_ids.append(book.get('id', ''))
                    else:
                        external_ids.append(book.external_id or f"temp_{book.id}")
                else:
                    local_ids.append(book.id)

            cache_data = {
                'local': local_ids,
                'external': external_ids,
                'has_external': bool(external_ids),
                'total': len(recommendations),
                'timestamp': timezone.now().isoformat()
            }

            self._cache.set(cache_key, cache_data)

        except Exception as e:
            logger.error(f"Erro ao atualizar cache: {str(e)}")

    def get_mixed_recommendations(self, user: User, limit: int = 20) -> Dict[str, Any]:
        """Obtém recomendações mistas com nova priorização"""
        try:
            # Usa o método principal que já retorna recomendações mistas
            recommendations = self.get_recommendations(user, limit)

            # Separa por tipo
            local_books = []
            external_books = []

            for book in recommendations:
                if self._is_external(book):
                    external_books.append(book)
                else:
                    local_books.append(book)

            return {
                'local': local_books,
                'external': external_books,
                'has_external': bool(external_books),
                'total': len(recommendations),
                'language_profile': self._language_provider.get_language_affinity(user)
            }

        except Exception as e:
            logger.error(f"Erro ao obter recomendações mistas: {str(e)}")
            return {
                'local': [],
                'external': [],
                'has_external': False,
                'total': 0,
                'language_profile': {}
            }

    def get_personalized_shelf(self, user: User, shelf_size: int = 20) -> Dict[str, Any]:
        """Gera prateleira personalizada com foco em preferências de idioma"""
        try:
            # Obtém recomendações mistas
            mixed_data = self.get_mixed_recommendations(user, limit=shelf_size)
            local_books = mixed_data.get('local', [])
            external_books = mixed_data.get('external', [])
            language_profile = mixed_data.get('language_profile', {})

            # Seções da prateleira
            sections = {
                'destaques': [],
                'seu_idioma': [],  # Nova seção para idioma preferido
                'based_on_history': [],  # Seção baseada no histórico
                'por_genero': {},
                'por_autor': {},
                'descobertas': []  # Nova seção para descobertas
            }

            # Obtém recomendações baseadas no histórico
            history_books = self._history_provider.get_recommendations(user, limit=8)
            sections['based_on_history'] = list(history_books)

            # Processa livros locais
            for book in local_books:
                # Destaques
                if len(sections['destaques']) < 5:
                    if book.e_destaque or book.quantidade_vendida > 10:
                        sections['destaques'].append(book)
                        continue

                # Seção de idioma preferido
                if (len(sections['seu_idioma']) < 8 and
                        language_profile.get('portuguese_preference', 0) > 0.5 and
                        book.idioma and self._language_provider._is_portuguese(book.idioma)):
                    sections['seu_idioma'].append(book)
                    continue

                # Por gênero
                if book.categoria:
                    categoria_principal = book.categoria.split(',')[0].strip()
                    if categoria_principal not in sections['por_genero']:
                        sections['por_genero'][categoria_principal] = []
                    if len(sections['por_genero'][categoria_principal]) < 5:
                        sections['por_genero'][categoria_principal].append(book)

                # Por autor
                if book.autor:
                    autor_principal = book.autor.split(',')[0].strip()
                    if autor_principal not in sections['por_autor']:
                        sections['por_autor'][autor_principal] = []
                    if len(sections['por_autor'][autor_principal]) < 3:
                        sections['por_autor'][autor_principal].append(book)

            # Adiciona descobertas (externos)
            sections['descobertas'] = external_books[:5]

            # Filtra seções vazias ou com poucos itens
            sections['por_genero'] = {
                k: v for k, v in sections['por_genero'].items()
                if len(v) > 1
            }
            sections['por_autor'] = {
                k: v for k, v in sections['por_autor'].items()
                if len(v) > 1
            }

            return {
                **sections,
                'has_external': bool(external_books),
                'total': len(local_books) + len(external_books),
                'language_preference': language_profile.get('portuguese_preference', 0)
            }

        except Exception as e:
            logger.error(f"Erro ao gerar prateleira personalizada: {str(e)}")
            return {
                'destaques': [],
                'seu_idioma': [],
                'based_on_history': [],
                'por_genero': {},
                'por_autor': {},
                'descobertas': [],
                'has_external': False,
                'total': 0,
                'language_preference': 0
            }

    def _get_cache_key(self, user: User) -> str:
        """Gera chave de cache única incluindo preferências de idioma"""
        try:
            # from django.utils import timezone # Removida pois já está importada no topo do módulo

            shelf_books = self._get_user_shelf_books(user)
            language_profile = self._language_provider.get_language_affinity(user)

            # Inclui preferência de idioma na chave
            language_hash = hash(str(language_profile.get('preferred_languages', {})))
            shelf_hash = hash(tuple(sorted(shelf_books)))

            # Adiciona timestamp para rotação de cache
            current_hour = timezone.now().hour

            cache_key = f'recommendations:v2:{user.id}:{shelf_hash}:{language_hash}:{current_hour}'
            return cache_key

        except Exception as e:
            logger.error(f"Erro ao gerar chave de cache: {str(e)}")
            return f'recommendations:v2:{user.id}:fallback'

    def _get_user_shelf_books(self, user: User) -> List[int]:
        """Obtém IDs dos livros nas prateleiras do usuário"""
        try:
            if not user:
                return []
            return list(UserBookShelf.objects.filter(
                user=user
            ).values_list('book_id', flat=True))
        except Exception as e:
            logger.error(f"Erro ao obter livros da prateleira: {str(e)}")
            return []

    def _get_fallback_recommendations(self, user: User, excluded_books: List[int], limit: int) -> List[Book]:
        """Recomendações de fallback priorizando português"""
        logger.warning("Usando recomendações de fallback")
        try:
            # Tenta primeiro livros em português
            portuguese_books = Book.objects.filter(
                Q(idioma__icontains='pt') |
                Q(idioma__icontains='por') |
                Q(idioma__icontains='brasil')
            ).exclude(
                id__in=excluded_books
            ).order_by('-quantidade_acessos', '?')[:limit]

            if portuguese_books.count() >= limit:
                return list(portuguese_books)

            # Complementa com outros livros
            remaining = limit - portuguese_books.count()
            other_books = Book.objects.exclude(
                id__in=excluded_books + list(portuguese_books.values_list('id', flat=True))
            ).order_by('-quantidade_vendida', '?')[:remaining]

            return list(portuguese_books) + list(other_books)

        except Exception as e:
            logger.error(f"Erro em recomendações fallback: {str(e)}")
            return []
# cgbookstore/apps/core/recommendations/providers/language_preference.py

from typing import List, Dict, Set, Tuple
from collections import Counter
from django.db.models import QuerySet, Q, Count, F
from django.contrib.auth import get_user_model
import logging

from ...models import Book, UserBookShelf, Profile
from .exclusion import ExclusionProvider

User = get_user_model()
logger = logging.getLogger(__name__)


class LanguagePreferenceProvider:
    """
    Provider de recomendações baseado em preferências de idioma do usuário.
    Analisa padrões de leitura por idioma e prioriza conteúdo em português
    ou no idioma preferido do usuário.
    """

    SHELF_WEIGHTS = {
        'favorito': 1.5,
        'lido': 2.0,
        'lendo': 2.5,
        'vou_ler': 1.0,
        'abandonei': -1.0
    }

    PORTUGUESE_VARIANTS = {
        'pt', 'pt-br', 'pt-pt', 'por', 'portuguese',
        'português', 'portugues', 'brazil', 'brasil'
    }

    def __init__(self):
        self.min_confidence_threshold = 0.7

    def get_recommendations(self, user: User, limit: int = 20) -> QuerySet:
        try:
            logger.info(f"=== Iniciando recomendações por idioma para usuário {user.id} ===")
            excluded_books = ExclusionProvider.get_excluded_books(user)
            language_profile = self._analyze_language_preferences(user)

            profile_preferences = {'interests_keywords': [], 'preferred_languages': []}
            if hasattr(user, 'profile'):
                profile_preferences = self._analyze_profile_preferences(user)

            if profile_preferences['preferred_languages']:
                for lang in profile_preferences['preferred_languages']:
                    language_profile['languages'][lang] = language_profile['languages'].get(lang, 0) + 1.0

            if not language_profile['languages']:
                logger.info("Usuário sem histórico de leitura. Retornando recomendações em português.")
                return self._get_portuguese_recommendations(excluded_books, limit)

            recommendations = self._build_language_based_recommendations(
                language_profile,
                excluded_books,
                limit,
                profile_preferences.get('interests_keywords', [])
            )

            logger.info(f"Total de recomendações por idioma: {recommendations.count()}")
            return recommendations

        except Exception as e:
            logger.error(f"Erro ao gerar recomendações por idioma: {str(e)}")
            return Book.objects.none()

    def _analyze_language_preferences(self, user: User) -> Dict:
        language_stats = {
            'languages': Counter(),
            'portuguese_preference': 0.0,
            'national_authors_preference': 0.0,
            'abandoned_languages': Counter(),
            'total_books': 0
        }
        user_shelves = UserBookShelf.objects.filter(user=user).select_related('book')

        for shelf in user_shelves:
            book = shelf.book
            weight = self.SHELF_WEIGHTS.get(shelf.shelf_type, 1.0)
            if book.idioma:
                normalized_language = self._normalize_language(book.idioma)
                if weight > 0:
                    language_stats['languages'][normalized_language] += weight
                    language_stats['total_books'] += 1
                    if self._is_portuguese(normalized_language):
                        language_stats['portuguese_preference'] += weight
                    if self._is_national_author(book.autor):
                        language_stats['national_authors_preference'] += weight
                else:
                    language_stats['abandoned_languages'][normalized_language] += abs(weight)

        if language_stats['total_books'] > 0:
            total_weight = sum(language_stats['languages'].values())
            language_stats['portuguese_percentage'] = (
                    language_stats['portuguese_preference'] / total_weight
            ) if total_weight > 0 else 0

        logger.info(f"Perfil de idioma do usuário: {language_stats}")
        return language_stats

    def _normalize_language(self, language: str) -> str:
        if not language:
            return 'unknown'
        normalized = language.lower().strip()
        if any(variant in normalized for variant in self.PORTUGUESE_VARIANTS):
            return 'pt'
        return normalized[:2] if len(normalized) >= 2 else normalized

    def _is_portuguese(self, language: str) -> bool:
        return self._normalize_language(language) == 'pt'

    def _is_national_author(self, author_name: str) -> bool:
        if not author_name:
            return False
        brazilian_surnames = {
            'silva', 'santos', 'oliveira', 'souza', 'rodrigues', 'ferreira', 'alves',
            'pereira', 'lima', 'gomes', 'costa', 'ribeiro', 'martins', 'carvalho',
            'almeida', 'lopes', 'soares', 'fernandes', 'vieira', 'barbosa', 'machado',
            'assis', 'amado', 'veríssimo', 'andrade', 'lispector', 'drummond',
            'meireles', 'lobato', 'telles', 'ramos', 'rosa', 'fonseca', 'coelho'
        }
        brazilian_authors = {
            'clarice lispector', 'machado de assis', 'jorge amado', 'paulo coelho',
            'érico veríssimo', 'graciliano ramos', 'guimarães rosa',
            'carlos drummond de andrade', 'cecília meireles', 'monteiro lobato',
            'lygia fagundes telles', 'rubem fonseca', 'nelson rodrigues',
            'rachel de queiroz', 'mário de andrade', 'oswald de andrade',
            'lima barreto', 'josé de alencar', 'joaquim manuel de macedo',
            'gonçalves dias'
        }
        author_lower = author_name.lower().strip()
        if author_lower in brazilian_authors:
            return True
        return any(surname in author_lower for surname in brazilian_surnames)

    def _build_language_based_recommendations(
            self, language_profile: Dict, excluded_books: Set[int],
            limit: int, interests_keywords: List[str] = None
    ) -> QuerySet:
        if interests_keywords is None:
            interests_keywords = []

        priority_languages = []
        if language_profile.get('portuguese_percentage', 0) > 0.6:
            priority_languages.append('pt')
        top_languages = [lang for lang, _ in language_profile['languages'].most_common(3)]
        priority_languages.extend(top_languages)
        priority_languages = list(dict.fromkeys(priority_languages))

        query = Q()
        for language in priority_languages[:3]:
            if self._is_portuguese(language):
                query |= Q(idioma__icontains='pt') | Q(idioma__icontains='por') | \
                         Q(idioma__icontains='brazil') | Q(idioma__icontains='brasil')
            else:
                query |= Q(idioma__icontains=language)

        if interests_keywords:
            interests_query = Q()
            for keyword in interests_keywords:
                interests_query |= Q(titulo__icontains=keyword) | Q(categoria__icontains=keyword)
            query |= interests_query

        if language_profile.get('national_authors_preference', 0) > 2.0:
            brazilian_authors_list = [
                'Machado de Assis', 'Clarice Lispector', 'Jorge Amado', 'Paulo Coelho',
                'Érico Veríssimo', 'Graciliano Ramos', 'Guimarães Rosa', 'Carlos Drummond',
                'Cecília Meireles', 'Monteiro Lobato', 'Lygia Fagundes Telles', 'Rubem Fonseca'
            ]
            author_query = Q()
            for author in brazilian_authors_list:
                author_query |= Q(autor__icontains=author)
            query |= author_query

        for abandoned_lang, count in language_profile.get('abandoned_languages', {}).items():
            if count > 2:
                query &= ~Q(idioma__icontains=abandoned_lang)

        recommendations = Book.objects.filter(query).exclude(id__in=excluded_books).distinct()

        if recommendations.count() < limit:
            current_ids = list(recommendations.values_list('id', flat=True))
            excluded_list_for_portuguese = list(excluded_books) + current_ids
            portuguese_books = self._get_portuguese_recommendations(
                set(excluded_list_for_portuguese),
                limit - recommendations.count()
            )
            if portuguese_books.exists():
                portuguese_ids = list(portuguese_books.values_list('id', flat=True))
                all_book_ids = current_ids + portuguese_ids
                recommendations = Book.objects.filter(id__in=all_book_ids).distinct()

        return recommendations.order_by('-quantidade_acessos', '?')[:limit]

    def _get_portuguese_recommendations(self, excluded_books: Set[int], limit: int) -> QuerySet:
        portuguese_query = Q()
        for variant in self.PORTUGUESE_VARIANTS:
            portuguese_query |= Q(idioma__icontains=variant)
        portuguese_query |= Q(autor__icontains='Machado') | Q(autor__icontains='Assis')
        portuguese_query |= Q(autor__icontains='Clarice') | Q(autor__icontains='Lispector')
        portuguese_query |= Q(autor__icontains='Jorge') & Q(autor__icontains='Amado')
        portuguese_query |= Q(autor__icontains='Paulo') & Q(autor__icontains='Coelho')

        return Book.objects.filter(portuguese_query).exclude(
            id__in=excluded_books
        ).distinct().order_by('-quantidade_vendida', '-quantidade_acessos', '?')[:limit]

    def get_language_affinity(self, user: User) -> Dict:
        profile_data = self._analyze_language_preferences(user)
        preferred_languages = dict(profile_data['languages']) if profile_data['languages'] else {}
        if not preferred_languages:
            preferred_languages = {'pt': 1.0}
        return {
            'preferred_languages': preferred_languages,
            'portuguese_preference': profile_data.get('portuguese_percentage', 0.0),
            'national_authors_preference': profile_data.get('national_authors_preference', 0.0),
            'avoided_languages': dict(profile_data.get('abandoned_languages', {}))
        }

    def _analyze_profile_preferences(self, user: User) -> Dict:
        # --- INÍCIO DA SEÇÃO DE DEBUG ---
        print(
            f"DEBUG _analyze_profile_preferences: Analisando perfil para user ID {user.id}, Username: {user.username}")
        # --- FIM DA SEÇÃO DE DEBUG ---
        preferences = {'interests_keywords': [], 'preferred_languages': []}
        try:
            profile_instance = user.profile
            # --- INÍCIO DA SEÇÃO DE DEBUG ---
            print(
                f"DEBUG _analyze_profile_preferences: profile_instance type: {type(profile_instance)}, content: {profile_instance}")
            if hasattr(profile_instance, 'interests'):
                print(
                    f"DEBUG _analyze_profile_preferences: profile_instance.interests content: '{profile_instance.interests}'")
            else:
                print(f"DEBUG _analyze_profile_preferences: profile_instance NÃO TEM ATRIBUTO interests.")
            # --- FIM DA SEÇÃO DE DEBUG ---

            if profile_instance and profile_instance.interests:
                # --- INÍCIO DA SEÇÃO DE DEBUG ---
                print(
                    f"DEBUG _analyze_profile_preferences: Entrou no IF (profile_instance and profile_instance.interests). Interests: '{profile_instance.interests}'")
                # --- FIM DA SEÇÃO DE DEBUG ---
                interests_lower = profile_instance.interests.lower()

                # Detecta menções a idiomas ou culturas - mais abrangente
                portuguese_terms = [
                    'português', 'portugues', 'brasil', 'brazil', 'portugal', 'lusófono', 'lusofo',
                    'literatura brasileira', 'brazilian', 'machado', 'cultura brasileira',
                    'machado de assis', 'clarice lispector', 'jorge amado'
                ]
                if any(term in interests_lower for term in portuguese_terms):
                    # --- INÍCIO DA SEÇÃO DE DEBUG ---
                    print(
                        f"DEBUG _analyze_profile_preferences: 'pt' SERÁ ADICIONADO. interests_lower: '{interests_lower}'")
                    # --- FIM DA SEÇÃO DE DEBUG ---
                    preferences['preferred_languages'].append('pt')

                english_terms = [
                    'english', 'inglês', 'ingles', 'americana', 'american', 'britânica', 'british'
                ]
                if any(term in interests_lower for term in english_terms):
                    # --- INÍCIO DA SEÇÃO DE DEBUG ---
                    print(
                        f"DEBUG _analyze_profile_preferences: 'en' SERÁ ADICIONADO. interests_lower: '{interests_lower}'")
                    # --- FIM DA SEÇÃO DE DEBUG ---
                    preferences['preferred_languages'].append('en')

                # Extrai palavras-chave para busca
                keywords = [
                    word.strip()
                    for word in interests_lower.split(',')
                    if len(word.strip()) > 3
                ]
                preferences['interests_keywords'] = keywords[:5]
                # --- INÍCIO DA SEÇÃO DE DEBUG ---
                print(f"DEBUG _analyze_profile_preferences: Keywords extraídos: {preferences['interests_keywords']}")
                # --- FIM DA SEÇÃO DE DEBUG ---
            else:
                # --- INÍCIO DA SEÇÃO DE DEBUG ---
                print(
                    f"DEBUG _analyze_profile_preferences: Condição (profile_instance and profile_instance.interests) foi FALSA.")
                if not profile_instance:
                    print(f"DEBUG _analyze_profile_preferences: Causa: profile_instance é falsy.")
                if profile_instance and not profile_instance.interests:  # Check se profile_instance existe mas interests não
                    print(
                        f"DEBUG _analyze_profile_preferences: Causa: profile_instance.interests é falsy: '{profile_instance.interests}'")
                # --- FIM DA SEÇÃO DE DEBUG ---

        except Profile.DoesNotExist:
            # --- INÍCIO DA SEÇÃO DE DEBUG ---
            print(f"DEBUG _analyze_profile_preferences: Profile.DoesNotExist para user ID {user.id}")
            # --- FIM DA SEÇÃO DE DEBUG ---
            logger.info(
                f"Perfil não encontrado para o usuário {user.id} em _analyze_profile_preferences. Usando defaults.")
        except AttributeError as ae:
            # --- INÍCIO DA SEÇÃO DE DEBUG ---
            print(f"DEBUG _analyze_profile_preferences: AttributeError para user ID {user.id}: {str(ae)}")
            # --- FIM DA SEÇÃO DE DEBUG ---
            logger.warning(
                f"Atributo 'profile' não encontrado no objeto User para o usuário {user.id}. Verifique a configuração da relação User-Profile.")
        except Exception as e:
            # --- INÍCIO DA SEÇÃO DE DEBUG ---
            print(
                f"DEBUG _analyze_profile_preferences: Exception para user ID {user.id}: {type(e).__name__} - {str(e)}")
            # --- FIM DA SEÇÃO DE DEBUG ---
            logger.warning(f"Erro inesperado ao analisar perfil para usuário {user.id}: {str(e)}")

        # --- INÍCIO DA SEÇÃO DE DEBUG ---
        print(f"DEBUG _analyze_profile_preferences: Retornando preferences: {preferences} para user ID {user.id}")
        # --- FIM DA SEÇÃO DE DEBUG ---
        return preferences
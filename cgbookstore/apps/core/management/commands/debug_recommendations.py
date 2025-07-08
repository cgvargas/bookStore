import json
import traceback
from datetime import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.cache import cache
from cgbookstore.apps.core.models.book import Book

# Imports opcionais - vamos testar se existem
try:
    from cgbookstore.apps.core.recommendations.engine import RecommendationEngine

    HAS_RECOMMENDATION_ENGINE = True
except ImportError:
    HAS_RECOMMENDATION_ENGINE = False
    RecommendationEngine = None

try:
    from cgbookstore.apps.core.services.google_books_service import GoogleBooksService

    HAS_GOOGLE_BOOKS_SERVICE = True
except ImportError:
    HAS_GOOGLE_BOOKS_SERVICE = False
    GoogleBooksService = None

try:
    # Tentar diferentes possíveis nomes/locais para External API
    from cgbookstore.apps.core.recommendations.providers.external_api import ExternalAPIProvider

    HAS_EXTERNAL_API_PROVIDER = True
except ImportError:
    try:
        from cgbookstore.apps.core.recommendations.providers.external_api import \
            GoogleBooksProvider as ExternalAPIProvider

        HAS_EXTERNAL_API_PROVIDER = True
    except ImportError:
        try:
            from cgbookstore.apps.core.services.google_books_client import GoogleBooksClient as ExternalAPIProvider

            HAS_EXTERNAL_API_PROVIDER = True
        except ImportError:
            HAS_EXTERNAL_API_PROVIDER = False
            ExternalAPIProvider = None

User = get_user_model()


class Command(BaseCommand):
    help = 'Diagnostica o sistema de recomendações em tempo real'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='ID do usuário para recomendações personalizadas'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Número de recomendações para testar (default: 10)'
        )
        parser.add_argument(
            '--test-images',
            action='store_true',
            help='Testa acessibilidade das URLs de imagens das recomendações'
        )
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Limpa cache de recomendações antes do teste'
        )
        parser.add_argument(
            '--engine-only',
            action='store_true',
            help='Testa apenas o motor de recomendações (sem APIs externas)'
        )
        parser.add_argument(
            '--api-only',
            action='store_true',
            help='Testa apenas as APIs externas'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('\n=== DIAGNÓSTICO SISTEMA RECOMENDAÇÕES ===\n')
        )

        # Verificar componentes disponíveis
        self._check_available_components()

        # Configurar parâmetros
        user_id = options.get('user_id')
        limit = options.get('limit', 10)

        # Limpar cache se solicitado
        if options.get('clear_cache'):
            self._clear_recommendations_cache()

        # Obter usuário se especificado
        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                self.stdout.write(f'👤 Usuário: {user.username} (ID: {user.id})')
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ Usuário ID {user_id} não encontrado'))
                return
        else:
            self.stdout.write('👤 Usuário: Anônimo (recomendações gerais)')

        self.stdout.write(f'🎯 Limite: {limit} recomendações\n')

        # Executar testes baseado nas opções e disponibilidade
        if options.get('api_only'):
            self._test_external_apis_only(limit, options)
        elif options.get('engine_only'):
            self._test_recommendation_engine_only(user, limit, options)
        else:
            # Teste completo
            self._test_full_recommendation_flow(user, limit, options)

    def _check_available_components(self):
        """Verifica quais componentes estão disponíveis"""
        self.stdout.write('🔍 VERIFICANDO COMPONENTES DISPONÍVEIS...\n')

        if HAS_RECOMMENDATION_ENGINE:
            self.stdout.write('✅ RecommendationEngine: Disponível')
        else:
            self.stdout.write('❌ RecommendationEngine: Não encontrado')

        if HAS_GOOGLE_BOOKS_SERVICE:
            self.stdout.write('✅ GoogleBooksService: Disponível')
        else:
            self.stdout.write('❌ GoogleBooksService: Não encontrado')

        if HAS_EXTERNAL_API_PROVIDER:
            self.stdout.write('✅ ExternalAPIProvider: Disponível')
        else:
            self.stdout.write('❌ ExternalAPIProvider: Não encontrado')

        self.stdout.write('')

    def _clear_recommendations_cache(self):
        """Limpa cache de recomendações"""
        self.stdout.write('🧹 LIMPANDO CACHE DE RECOMENDAÇÕES...\n')

        try:
            # Tentar limpar via padrões
            from django.core.cache import caches
            default_cache = caches['default']
            client = default_cache.client.get_client(write=True)

            patterns = ['*recommend*', '*recomend*', '*google_books*', '*external*']
            total_cleared = 0

            for pattern in patterns:
                keys = client.keys(pattern)
                if keys:
                    deleted = client.delete(*keys)
                    total_cleared += deleted
                    self.stdout.write(f'   🗑️ Padrão "{pattern}": {deleted} chaves removidas')

            self.stdout.write(f'✅ Total: {total_cleared} chaves removidas\n')

        except Exception as e:
            self.stdout.write(f'❌ Erro ao limpar cache: {e}\n')

    def _test_full_recommendation_flow(self, user, limit, options):
        """Testa o fluxo completo de recomendações"""
        self.stdout.write('🔄 TESTANDO FLUXO COMPLETO DE RECOMENDAÇÕES...\n')

        if not HAS_RECOMMENDATION_ENGINE:
            self.stdout.write(
                self.style.WARNING('⚠️ RecommendationEngine não disponível - pulando para livros do banco'))
            self._test_recommendation_engine_only(user, limit, options)
            return

        try:
            # 1. Testar motor de recomendações
            engine = RecommendationEngine()
            self.stdout.write('📊 Iniciando motor de recomendações...')

            start_time = datetime.now()
            recommendations = engine.get_recommendations(user=user, limit=limit)
            end_time = datetime.now()

            processing_time = (end_time - start_time).total_seconds()
            self.stdout.write(f'⏱️ Tempo de processamento: {processing_time:.2f}s')
            self.stdout.write(f'📋 Recomendações obtidas: {len(recommendations)}')

            if not recommendations:
                self.stdout.write(self.style.WARNING('⚠️ Nenhuma recomendação retornada'))
                return

            # 2. Analisar estrutura das recomendações
            self._analyze_recommendations_structure(recommendations, options)

            # 3. Verificar cache
            self._check_recommendations_cache(user)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro no fluxo de recomendações: {e}'))
            self.stdout.write(f'Traceback: {traceback.format_exc()}')

            # Fallback para livros do banco
            self.stdout.write('\n🔄 Tentando fallback para livros do banco...')
            self._test_recommendation_engine_only(user, limit, options)

    def _test_recommendation_engine_only(self, user, limit, options):
        """Testa apenas o motor de recomendações (sem APIs)"""
        self.stdout.write('⚙️ TESTANDO APENAS MOTOR DE RECOMENDAÇÕES...\n')

        try:
            # Buscar livros existentes no banco
            books = Book.objects.all()[:limit]

            self.stdout.write(f'📚 Livros no banco: {books.count()}')

            if not books.exists():
                self.stdout.write(self.style.WARNING('⚠️ Nenhum livro encontrado no banco'))
                return

            # Analisar livros do banco
            self._analyze_database_books(books, options)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro no motor: {e}'))

    def _test_external_apis_only(self, limit, options):
        """Testa apenas as APIs externas"""
        self.stdout.write('🌐 TESTANDO APENAS APIS EXTERNAS...\n')

        try:
            # 1. Testar Google Books Service
            self._test_google_books_service(limit)

            # 2. Testar External API Provider
            self._test_external_api_provider(limit)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro nas APIs: {e}'))

    def _analyze_recommendations_structure(self, recommendations, options):
        """Analisa a estrutura das recomendações retornadas"""
        self.stdout.write('\n🔍 ANALISANDO ESTRUTURA DAS RECOMENDAÇÕES...\n')

        for i, rec in enumerate(recommendations[:5], 1):
            self.stdout.write(f'📖 RECOMENDAÇÃO {i}:')

            # Analisar tipo do objeto
            rec_type = type(rec).__name__
            self.stdout.write(f'   Tipo: {rec_type}')

            if hasattr(rec, '__dict__'):
                # É um objeto modelo
                self._analyze_book_object(rec, i, options)
            elif isinstance(rec, dict):
                # É um dicionário
                self._analyze_book_dict(rec, i, options)
            else:
                self.stdout.write(f'   ❓ Tipo desconhecido: {rec}')

            self.stdout.write('')

    def _analyze_book_object(self, book, index, options):
        """Analisa objeto Book"""
        self.stdout.write(f'   ID: {getattr(book, "id", "N/A")}')
        self.stdout.write(f'   Título: {getattr(book, "titulo", "N/A")}')
        self.stdout.write(f'   External ID: {getattr(book, "external_id", "N/A")}')

        # Analisar URL da capa
        capa_url = getattr(book, 'capa_url', None)
        if capa_url:
            self.stdout.write(f'   Capa URL: {capa_url}')
            self._analyze_image_url(capa_url, f'Recomendação {index}', options)
        else:
            self.stdout.write('   ❌ Sem URL de capa')

    def _analyze_book_dict(self, book_dict, index, options):
        """Analisa dicionário de livro"""

        # Debug: mostrar estrutura completa
        self.stdout.write(f'   📋 Estrutura completa: {list(book_dict.keys())}')

        # Verificar se tem volumeInfo
        if 'volumeInfo' in book_dict:
            vol_info = book_dict['volumeInfo']
            self.stdout.write(f'   📖 volumeInfo chaves: {list(vol_info.keys())}')

            title = vol_info.get('title', 'N/A')
            authors = vol_info.get('authors', [])
            author_str = ', '.join(authors) if isinstance(authors, list) else str(authors)

            self.stdout.write(f'   Título: {title}')
            self.stdout.write(f'   Autor(es): {author_str}')

            # Verificar imageLinks
            if 'imageLinks' in vol_info:
                image_links = vol_info['imageLinks']
                self.stdout.write(f'   🖼️ imageLinks: {image_links}')

                for img_type, img_url in image_links.items():
                    if img_url:
                        self.stdout.write(f'     {img_type}: {img_url}')
                        self._analyze_image_url(img_url, f'Recomendação {index} (volumeInfo.imageLinks.{img_type})',
                                                options)
            else:
                self.stdout.write('   ❌ Sem imageLinks em volumeInfo')

        # Verificar dados no nível raiz também
        root_fields = ['title', 'titulo', 'image_url', 'capa_url', 'thumbnail']
        for field in root_fields:
            if field in book_dict and book_dict[field]:
                value = book_dict[field]
                self.stdout.write(f'   {field} (raiz): {value}')
                if any(img_key in field.lower() for img_key in ['image', 'capa', 'thumbnail']):
                    self._analyze_image_url(value, f'Recomendação {index} (raiz.{field})', options)

        book_id = book_dict.get('id', 'N/A')
        external_id = book_dict.get('external_id', book_id)

        self.stdout.write(f'   ID: {book_id}')
        self.stdout.write(f'   External ID: {external_id}')

    def _analyze_image_url(self, url, location, options):
        """Analisa URL de imagem"""
        if not url or not url.strip():
            self.stdout.write(f'     ❌ URL vazia em {location}')
            return

        # Verificar problemas comuns
        issues = []
        if url.startswith('http://'):
            issues.append('HTTP em vez de HTTPS')
        if '\\' in url:
            issues.append('Barras incorretas')
        if not url.startswith(('http://', 'https://', '/')):
            issues.append('URL malformada')

        if issues:
            self.stdout.write(f'     ⚠️ Problemas em {location}: {", ".join(issues)}')
        else:
            self.stdout.write(f'     ✅ URL válida em {location}')

        # Testar acessibilidade se solicitado
        if options.get('test_images'):
            self._test_image_url_accessibility(url, location)

    def _test_image_url_accessibility(self, url, location):
        """Testa se a URL da imagem está acessível"""
        try:
            import requests

            # Ajustar URL se for local
            if url.startswith('/media'):
                test_url = f'http://127.0.0.1:8000{url}'
            else:
                test_url = url

            response = requests.head(test_url, timeout=5, allow_redirects=True)

            if response.status_code == 200:
                self.stdout.write(f'     🌐 ✅ Acessível (200) - {location}')
            else:
                self.stdout.write(f'     🌐 ❌ Status {response.status_code} - {location}')

        except requests.exceptions.ConnectionError:
            self.stdout.write(f'     🌐 ❌ Erro de conexão - {location}')
        except Exception as e:
            self.stdout.write(f'     🌐 ❌ Erro: {e} - {location}')

    def _analyze_database_books(self, books, options):
        """Analisa livros do banco de dados"""
        self.stdout.write('\n📚 ANALISANDO LIVROS DO BANCO...\n')

        for i, book in enumerate(books[:5], 1):
            self.stdout.write(f'📖 LIVRO {i}:')
            self._analyze_book_object(book, i, options)
            self.stdout.write('')

    def _test_google_books_service(self, limit):
        """Testa Google Books Service"""
        self.stdout.write('📚 TESTANDO GOOGLE BOOKS SERVICE...\n')

        if not HAS_GOOGLE_BOOKS_SERVICE:
            self.stdout.write('❌ GoogleBooksService não disponível')
            return

        try:
            service = GoogleBooksService()

            # Testar busca por query genérica
            query = "python programming"
            self.stdout.write(f'🔍 Buscando: "{query}"')

            results = service.search_books(query, max_results=limit)

            if results:
                self.stdout.write(f'✅ {len(results)} resultados encontrados')

                # Analisar primeiro resultado
                if results:
                    first_result = results[0]
                    self.stdout.write(f'   Primeiro resultado: {first_result}')
            else:
                self.stdout.write('❌ Nenhum resultado encontrado')

        except Exception as e:
            self.stdout.write(f'❌ Erro no Google Books Service: {e}')

    def _test_external_api_provider(self, limit):
        """Testa External API Provider"""
        self.stdout.write('\n🔌 TESTANDO EXTERNAL API PROVIDER...\n')

        if not HAS_EXTERNAL_API_PROVIDER:
            self.stdout.write('❌ ExternalAPIProvider não disponível')
            return

        try:
            provider = ExternalAPIProvider()

            # Testar obtenção de recomendações
            self.stdout.write('🎯 Obtendo recomendações via API externa...')

            recommendations = provider.get_recommendations(limit=limit)

            if recommendations:
                self.stdout.write(f'✅ {len(recommendations)} recomendações obtidas')

                # Analisar primeira recomendação
                if recommendations:
                    first_rec = recommendations[0]
                    self.stdout.write(f'   Primeira recomendação: {first_rec}')
            else:
                self.stdout.write('❌ Nenhuma recomendação obtida')

        except Exception as e:
            self.stdout.write(f'❌ Erro no External API Provider: {e}')
            self.stdout.write(f'Traceback: {traceback.format_exc()}')

    def _check_recommendations_cache(self, user):
        """Verifica cache de recomendações"""
        self.stdout.write('\n💾 VERIFICANDO CACHE DE RECOMENDAÇÕES...\n')

        try:
            # Chaves de cache possíveis
            cache_keys = [
                f'recommendations_{user.id if user else "anonymous"}',
                f'user_recommendations_{user.id if user else "0"}',
                'general_recommendations',
                'mixed_recommendations',
                'external_api_recommendations'
            ]

            found_cache = False

            for cache_key in cache_keys:
                cached_data = cache.get(cache_key)

                if cached_data is not None:
                    found_cache = True
                    self.stdout.write(f'✅ Cache encontrado: {cache_key}')
                    self.stdout.write(f'   Tipo: {type(cached_data).__name__}')

                    if isinstance(cached_data, (list, dict)):
                        self.stdout.write(f'   Itens: {len(cached_data)}')

                    # Verificar TTL se possível
                    try:
                        from django.core.cache import caches
                        default_cache = caches['default']
                        client = default_cache.client.get_client(write=True)
                        ttl = client.ttl(f'default:1:{cache_key}')

                        if ttl > 0:
                            self.stdout.write(f'   TTL: {ttl}s ({ttl // 60}m {ttl % 60}s)')
                        elif ttl == -1:
                            self.stdout.write(f'   TTL: Sem expiração')
                        else:
                            self.stdout.write(f'   TTL: Expirado ou inexistente')
                    except:
                        pass
                else:
                    self.stdout.write(f'❌ Cache não encontrado: {cache_key}')

            if not found_cache:
                self.stdout.write('⚠️ Nenhum cache de recomendações encontrado')

        except Exception as e:
            self.stdout.write(f'❌ Erro ao verificar cache: {e}')

    def _format_recommendations_summary(self, recommendations):
        """Formata resumo das recomendações"""
        summary = {
            'total': len(recommendations),
            'with_images': 0,
            'without_images': 0,
            'local_images': 0,
            'remote_images': 0,
            'broken_paths': 0
        }

        for rec in recommendations:
            capa_url = None

            if hasattr(rec, 'capa_url'):
                capa_url = rec.capa_url
            elif isinstance(rec, dict):
                capa_url = rec.get('capa_url') or rec.get('image_url')

            if capa_url:
                summary['with_images'] += 1

                if capa_url.startswith('/media'):
                    summary['local_images'] += 1
                elif capa_url.startswith('http'):
                    summary['remote_images'] += 1

                if '\\' in capa_url:
                    summary['broken_paths'] += 1
            else:
                summary['without_images'] += 1

        return summary
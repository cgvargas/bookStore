# cgbookstore/apps/core/management/commands/performance_diagnostics.py
"""
Comando para diagnóstico completo de performance do sistema CGBookstore.
Analisa banco de dados, cache, APIs, memória e detecta gargalos automaticamente.

Uso:
    python manage.py performance_diagnostics --quick
    python manage.py performance_diagnostics --deep --output json --save-report relatorio.json
"""

import time
import statistics
import gc
import json
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core.cache import caches
from django.db import connection
from django.conf import settings
from django.contrib.auth import get_user_model
from cgbookstore.apps.core.models.book import Book

# Importações condicionais para modelos que podem estar em locais diferentes
try:
    from cgbookstore.apps.core.models.user import UserBookShelf
except ImportError:
    try:
        from cgbookstore.apps.core.models import UserBookShelf
    except ImportError:
        # Se não encontrar, vamos definir como None e lidar com isso
        UserBookShelf = None

try:
    from cgbookstore.apps.core.recommendations.engine import RecommendationEngine
except ImportError:
    RecommendationEngine = None

try:
    from cgbookstore.apps.core.services.google_books_service import GoogleBooksClient
except ImportError:
    try:
        from cgbookstore.apps.core.services.google_books_client import GoogleBooksClient
    except ImportError:
        GoogleBooksClient = None

# Importação condicional do psutil
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

User = get_user_model()


class Command(BaseCommand):
    help = 'Executa diagnóstico completo de performance do sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--quick',
            action='store_true',
            help='Executa apenas testes rápidos (< 30s)'
        )
        parser.add_argument(
            '--deep',
            action='store_true',
            help='Executa análise profunda (pode demorar vários minutos)'
        )
        parser.add_argument(
            '--output',
            type=str,
            choices=['console', 'json', 'html'],
            default='console',
            help='Formato de saída do relatório'
        )
        parser.add_argument(
            '--save-report',
            type=str,
            help='Salvar relatório em arquivo'
        )

    def handle(self, *args, **options):
        self.options = options
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'system_info': {},
            'database_performance': {},
            'cache_performance': {},
            'api_performance': {},
            'recommendations_performance': {},
            'memory_usage': {},
            'bottlenecks': [],
            'recommendations': []
        }

        self.stdout.write(
            self.style.SUCCESS('\n🚀 DIAGNÓSTICO DE PERFORMANCE CGBookstore\n')
        )

        # Executar diagnósticos
        self._collect_system_info()
        self._test_database_performance()
        self._test_cache_performance()
        self._test_api_performance()
        self._test_recommendations_performance()
        self._analyze_memory_usage()

        if options['deep']:
            self._deep_analysis()

        # Análise e recomendações
        self._analyze_bottlenecks()
        self._generate_recommendations()

        # Gerar relatório
        self._output_results()

    def _collect_system_info(self):
        """Coleta informações do sistema"""
        self.stdout.write('📊 Coletando informações do sistema...')

        try:
            if PSUTIL_AVAILABLE:
                # Informações de CPU e memória com psutil
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')

                self.results['system_info'] = {
                    'cpu_percent': cpu_percent,
                    'memory_total_gb': round(memory.total / (1024 ** 3), 2),
                    'memory_used_gb': round(memory.used / (1024 ** 3), 2),
                    'memory_percent': memory.percent,
                    'disk_total_gb': round(disk.total / (1024 ** 3), 2),
                    'disk_used_gb': round(disk.used / (1024 ** 3), 2),
                    'disk_percent': (disk.used / disk.total) * 100,
                    'python_version': f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}",
                    'django_debug': settings.DEBUG
                }

                self.stdout.write(f'   CPU: {cpu_percent}%')
                self.stdout.write(f'   Memória: {memory.percent}% ({memory.used // (1024 ** 2)} MB)')
                self.stdout.write(f'   Disco: {(disk.used / disk.total) * 100:.1f}%')
            else:
                # Informações básicas sem psutil
                import sys
                self.results['system_info'] = {
                    'python_version': f"{sys.version_info.major}.{sys.version_info.minor}",
                    'django_debug': settings.DEBUG,
                    'psutil_available': False
                }
                self.stdout.write('   ⚠️ psutil não disponível - informações limitadas')
                self.stdout.write(f'   Python: {sys.version_info.major}.{sys.version_info.minor}')
                self.stdout.write(f'   Debug: {settings.DEBUG}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   Erro ao coletar info do sistema: {e}'))

    def _test_database_performance(self):
        """Testa performance do banco de dados"""
        self.stdout.write('\n🗃️ Testando performance do banco de dados...')

        try:
            # Limpar queries anteriores
            connection.queries_log.clear()

            # Teste 1: Consulta simples
            start_time = time.time()
            book_count = Book.objects.count()
            simple_query_time = time.time() - start_time

            # Teste 2: Consulta complexa com joins (adaptável se UserBookShelf não existir)
            start_time = time.time()
            try:
                if UserBookShelf:
                    # Tenta encontrar o relacionamento correto
                    books_with_shelves = Book.objects.select_related().prefetch_related(
                        'userbookshelf_set'
                    )[:10]
                else:
                    # Fallback sem relacionamento
                    books_with_shelves = Book.objects.select_related()[:10]
            except Exception:
                # Se der erro no relacionamento, usa consulta simples
                books_with_shelves = Book.objects.all()[:10]

            list(books_with_shelves)  # Forçar execução
            complex_query_time = time.time() - start_time

            # Teste 3: Múltiplas consultas
            start_time = time.time()
            for i in range(10):
                Book.objects.filter(id__lte=i + 1).exists()
            multiple_queries_time = time.time() - start_time

            # Análise de queries
            total_queries = len(connection.queries)
            total_time = sum(float(q['time']) for q in connection.queries)

            self.results['database_performance'] = {
                'total_books': book_count,
                'simple_query_time': simple_query_time,
                'complex_query_time': complex_query_time,
                'multiple_queries_time': multiple_queries_time,
                'total_queries_executed': total_queries,
                'total_db_time': total_time,
                'average_query_time': total_time / total_queries if total_queries > 0 else 0,
                'slow_queries': [q for q in connection.queries if float(q['time']) > 0.1],
                'userbookshelf_available': UserBookShelf is not None
            }

            self.stdout.write(f'   📚 Total de livros: {book_count}')
            self.stdout.write(f'   ⚡ Consulta simples: {simple_query_time:.4f}s')
            self.stdout.write(f'   🔗 Consulta com joins: {complex_query_time:.4f}s')
            self.stdout.write(f'   📊 {total_queries} queries em {total_time:.4f}s')

            if self.results['database_performance']['slow_queries']:
                self.stdout.write(self.style.WARNING(
                    f'   ⚠️ {len(self.results["database_performance"]["slow_queries"])} queries lentas detectadas'))

            if not UserBookShelf:
                self.stdout.write(self.style.WARNING('   ⚠️ UserBookShelf não encontrado - testes limitados'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   Erro no teste de DB: {e}'))

    def _test_cache_performance(self):
        """Testa performance do sistema de cache"""
        self.stdout.write('\n💾 Testando performance do cache...')

        cache_results = {}

        for cache_name in ['default', 'recommendations', 'google_books', 'image_proxy']:
            try:
                cache = caches[cache_name]

                # Teste de escrita
                test_data = {'test': 'data', 'number': 12345, 'list': [1, 2, 3, 4, 5]}

                start_time = time.time()
                for i in range(100):
                    cache.set(f'perf_test_{i}', test_data, 300)
                write_time = time.time() - start_time

                # Teste de leitura
                start_time = time.time()
                hits = 0
                for i in range(100):
                    if cache.get(f'perf_test_{i}') is not None:
                        hits += 1
                read_time = time.time() - start_time

                # Limpeza
                for i in range(100):
                    cache.delete(f'perf_test_{i}')

                cache_results[cache_name] = {
                    'write_time': write_time,
                    'read_time': read_time,
                    'hit_rate': hits / 100,
                    'avg_write_time': write_time / 100,
                    'avg_read_time': read_time / 100,
                    'status': 'ok' if hits > 90 else 'warning'
                }

                self.stdout.write(f'   🔧 {cache_name}: Write {write_time:.4f}s, Read {read_time:.4f}s, Hits {hits}%')

            except Exception as e:
                cache_results[cache_name] = {
                    'error': str(e),
                    'status': 'error'
                }
                self.stdout.write(self.style.ERROR(f'   ❌ {cache_name}: {e}'))

        self.results['cache_performance'] = cache_results

    def _test_api_performance(self):
        """Testa performance das APIs"""
        self.stdout.write('\n🌐 Testando performance das APIs...')

        try:
            if not GoogleBooksClient:
                self.stdout.write(self.style.WARNING('   ⚠️ GoogleBooksClient não encontrado - pulando testes de API'))
                self.results['api_performance'] = {
                    'google_books_available': False,
                    'message': 'GoogleBooksClient não disponível'
                }
                return

            # Teste Google Books API
            client = GoogleBooksClient(context="performance_test")

            # Múltiplas consultas para medir média
            times = []
            for query in ['python', 'django', 'programming', 'fiction', 'science']:
                start_time = time.time()
                try:
                    results = client.search_books(query, max_results=5)
                    elapsed = time.time() - start_time
                    times.append(elapsed)
                    self.stdout.write(f'   📖 "{query}": {elapsed:.3f}s ({len(results) if results else 0} resultados)')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'   ⚠️ "{query}": {e}'))

            if times:
                self.results['api_performance'] = {
                    'google_books_avg_time': statistics.mean(times),
                    'google_books_min_time': min(times),
                    'google_books_max_time': max(times),
                    'google_books_total_calls': len(times),
                    'google_books_success_rate': len(times) / 5,
                    'google_books_available': True
                }
            else:
                self.results['api_performance'] = {
                    'google_books_available': True,
                    'message': 'Nenhuma consulta bem-sucedida'
                }

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   Erro no teste de API: {e}'))
            self.results['api_performance'] = {
                'error': str(e),
                'google_books_available': False
            }

    def _test_recommendations_performance(self):
        """Testa performance do sistema de recomendações"""
        self.stdout.write('\n🎯 Testando performance das recomendações...')

        try:
            if not RecommendationEngine:
                self.stdout.write(self.style.WARNING('   ⚠️ RecommendationEngine não encontrado - pulando testes'))
                self.results['recommendations_performance'] = {
                    'recommendation_engine_available': False,
                    'message': 'RecommendationEngine não disponível'
                }
                return

            engine = RecommendationEngine()

            # Teste para usuário anônimo
            start_time = time.time()
            anon_recommendations = engine.get_recommendations(user=None, limit=10)
            anon_time = time.time() - start_time

            # Teste para usuário logado (se existir)
            user_time = None
            user_recommendations = []
            try:
                user = User.objects.first()
                if user:
                    start_time = time.time()
                    user_recommendations = engine.get_recommendations(user=user, limit=10)
                    user_time = time.time() - start_time
            except Exception:
                pass

            self.results['recommendations_performance'] = {
                'anonymous_time': anon_time,
                'anonymous_count': len(anon_recommendations),
                'user_time': user_time,
                'user_count': len(user_recommendations) if user_recommendations else 0,
                'recommendation_engine_available': True
            }

            self.stdout.write(f'   👤 Anônimo: {anon_time:.3f}s ({len(anon_recommendations)} recomendações)')
            if user_time:
                self.stdout.write(f'   🔐 Usuário: {user_time:.3f}s ({len(user_recommendations)} recomendações)')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   Erro no teste de recomendações: {e}'))
            self.results['recommendations_performance'] = {
                'error': str(e),
                'recommendation_engine_available': False
            }

    def _analyze_memory_usage(self):
        """Analisa uso de memória"""
        self.stdout.write('\n🧠 Analisando uso de memória...')

        try:
            # Força garbage collection
            gc.collect()

            if PSUTIL_AVAILABLE:
                # Informações de memória com psutil
                memory = psutil.virtual_memory()
                process = psutil.Process()
                process_memory = process.memory_info()

                self.results['memory_usage'] = {
                    'system_memory_percent': memory.percent,
                    'process_memory_mb': process_memory.rss / (1024 * 1024),
                    'process_memory_percent': process.memory_percent(),
                    'gc_objects': len(gc.get_objects()),
                    'gc_collections': gc.get_stats() if hasattr(gc, 'get_stats') else None
                }

                self.stdout.write(f'   📊 Sistema: {memory.percent}%')
                self.stdout.write(f'   🔧 Processo: {process_memory.rss // (1024 * 1024)} MB')
                self.stdout.write(f'   🗑️ Objetos GC: {len(gc.get_objects())}')
            else:
                # Análise básica sem psutil
                self.results['memory_usage'] = {
                    'gc_objects': len(gc.get_objects()),
                    'gc_collections': gc.get_stats() if hasattr(gc, 'get_stats') else None,
                    'psutil_available': False
                }
                self.stdout.write(f'   🗑️ Objetos GC: {len(gc.get_objects())}')
                self.stdout.write('   ⚠️ psutil não disponível - análise limitada')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   Erro na análise de memória: {e}'))

    def _deep_analysis(self):
        """Análise profunda (apenas se --deep for especificado)"""
        self.stdout.write('\n🔬 Executando análise profunda...')

        try:
            # Teste de stress no banco de dados
            self.stdout.write('   Teste de stress do banco...')
            start_time = time.time()

            # Simula múltiplas consultas simultâneas
            for i in range(50):
                books = Book.objects.filter(titulo__icontains='a')[:5]
                list(books)

            stress_time = time.time() - start_time
            self.stdout.write(f'   📈 Stress test: {stress_time:.3f}s (50 consultas)')

            # Teste de cache sob carga
            self.stdout.write('   Teste de cache sob carga...')
            cache = caches['default']

            start_time = time.time()
            for i in range(1000):
                cache.set(f'stress_test_{i}', f'data_{i}', 60)
            cache_stress_time = time.time() - start_time

            self.stdout.write(f'   💾 Cache stress: {cache_stress_time:.3f}s (1000 operações)')

            # Adiciona aos resultados
            if 'deep_analysis' not in self.results:
                self.results['deep_analysis'] = {}

            self.results['deep_analysis'].update({
                'database_stress_time': stress_time,
                'cache_stress_time': cache_stress_time
            })

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   Erro na análise profunda: {e}'))

    def _analyze_bottlenecks(self):
        """Identifica gargalos de performance"""
        bottlenecks = []

        # Análise de DB
        db_perf = self.results.get('database_performance', {})
        if db_perf.get('complex_query_time', 0) > 1.0:
            bottlenecks.append({
                'type': 'database',
                'severity': 'high',
                'message': f'Consultas complexas muito lentas ({db_perf["complex_query_time"]:.2f}s)'
            })

        if len(db_perf.get('slow_queries', [])) > 0:
            bottlenecks.append({
                'type': 'database',
                'severity': 'medium',
                'message': f'{len(db_perf["slow_queries"])} queries lentas detectadas'
            })

        # Análise de Cache
        cache_perf = self.results.get('cache_performance', {})
        for cache_name, stats in cache_perf.items():
            if isinstance(stats, dict) and stats.get('hit_rate', 1) < 0.8:
                bottlenecks.append({
                    'type': 'cache',
                    'severity': 'medium',
                    'message': f'Cache {cache_name} com baixa taxa de hit ({stats["hit_rate"] * 100:.1f}%)'
                })

        # Análise de API
        api_perf = self.results.get('api_performance', {})
        if api_perf.get('google_books_avg_time', 0) > 2.0:
            bottlenecks.append({
                'type': 'api',
                'severity': 'medium',
                'message': f'Google Books API lenta (média {api_perf["google_books_avg_time"]:.2f}s)'
            })

        # Análise de Memória
        memory = self.results.get('memory_usage', {})
        if memory.get('system_memory_percent', 0) > 80:
            bottlenecks.append({
                'type': 'memory',
                'severity': 'high',
                'message': f'Uso alto de memória do sistema ({memory["system_memory_percent"]:.1f}%)'
            })

        self.results['bottlenecks'] = bottlenecks

    def _generate_recommendations(self):
        """Gera recomendações de otimização"""
        recommendations = []

        bottlenecks = self.results.get('bottlenecks', [])

        for bottleneck in bottlenecks:
            if bottleneck['type'] == 'database':
                if 'queries lentas' in bottleneck['message']:
                    recommendations.append({
                        'category': 'database',
                        'priority': 'high',
                        'action': 'Otimizar queries lentas',
                        'details': 'Revisar queries que demoram > 0.1s, adicionar índices, usar select_related/prefetch_related'
                    })
                elif 'consultas complexas' in bottleneck['message']:
                    recommendations.append({
                        'category': 'database',
                        'priority': 'medium',
                        'action': 'Otimizar consultas complexas',
                        'details': 'Implementar cache para consultas complexas, dividir em consultas menores'
                    })

            elif bottleneck['type'] == 'cache':
                recommendations.append({
                    'category': 'cache',
                    'priority': 'medium',
                    'action': 'Melhorar estratégia de cache',
                    'details': 'Revisar TTL, implementar cache warming, verificar invalidação'
                })

            elif bottleneck['type'] == 'api':
                recommendations.append({
                    'category': 'api',
                    'priority': 'medium',
                    'action': 'Otimizar chamadas de API',
                    'details': 'Implementar timeout menor, cache mais agressivo, fallbacks'
                })

            elif bottleneck['type'] == 'memory':
                recommendations.append({
                    'category': 'memory',
                    'priority': 'high',
                    'action': 'Otimizar uso de memória',
                    'details': 'Aumentar memória do servidor ou otimizar código Python'
                })

        # Recomendações gerais
        if not bottlenecks:
            recommendations.append({
                'category': 'general',
                'priority': 'low',
                'action': 'Sistema em boa performance',
                'details': 'Continue monitorando métricas regularmente'
            })

        self.results['recommendations'] = recommendations

    def _output_results(self):
        """Gera relatório final"""
        self.stdout.write('\n📋 RELATÓRIO FINAL:\n')

        # Resumo executivo
        total_bottlenecks = len(self.results['bottlenecks'])
        high_priority = len([b for b in self.results['bottlenecks'] if b['severity'] == 'high'])

        if high_priority > 0:
            self.stdout.write(self.style.ERROR(f'🚨 {high_priority} problemas críticos detectados'))
        elif total_bottlenecks > 0:
            self.stdout.write(self.style.WARNING(f'⚠️ {total_bottlenecks} problemas detectados'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ Sistema em boa performance'))

        # Bottlenecks
        if self.results['bottlenecks']:
            self.stdout.write('\n🔍 GARGALOS IDENTIFICADOS:')
            for b in self.results['bottlenecks']:
                severity_icon = '🚨' if b['severity'] == 'high' else '⚠️'
                self.stdout.write(f'   {severity_icon} {b["message"]}')

        # Recomendações
        if self.results['recommendations']:
            self.stdout.write('\n💡 RECOMENDAÇÕES:')
            for r in self.results['recommendations']:
                priority_icon = '🔴' if r['priority'] == 'high' else '🟡' if r['priority'] == 'medium' else '🟢'
                self.stdout.write(f'   {priority_icon} {r["action"]}')
                self.stdout.write(f'      {r["details"]}')

        # Salvar relatório se solicitado
        if self.options.get('save_report'):
            self._save_report()

    def _save_report(self):
        """Salva relatório em arquivo"""
        try:
            filename = self.options['save_report']

            with open(filename, 'w', encoding='utf-8') as f:
                if filename.endswith('.json'):
                    json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
                else:
                    # Formato texto
                    f.write(f"Performance Report - {self.results['timestamp']}\n")
                    f.write("=" * 50 + "\n\n")

                    for section, data in self.results.items():
                        if section not in ['timestamp']:
                            f.write(f"{section.upper()}:\n")
                            f.write(str(data) + "\n\n")

            self.stdout.write(self.style.SUCCESS(f'📄 Relatório salvo em: {filename}'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao salvar relatório: {e}'))
# cgbookstore/apps/core/management/commands/quick_performance_check.py

import time
import threading
from django.core.management.base import BaseCommand
from django.db import connection, connections
from django.core.cache import caches
from django.conf import settings


class Command(BaseCommand):
    help = 'Diagnóstico rápido de performance para identificar causa raiz da lentidão'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔍 DIAGNÓSTICO RÁPIDO DE PERFORMANCE\n')
        )

        # Teste 1: Conexão básica com o banco (com timeout)
        self.test_basic_db_connection()

        # Teste 2: Verificar configurações problemáticas
        self.check_problematic_settings()

        # Teste 3: Teste individual de cada cache
        self.test_individual_caches()

        # Teste 4: Verificar queries ativas/locks
        self.check_active_queries()

        # Teste 5: Teste de importação de modelos
        self.test_model_imports()

        # Teste 6: Verificar middlewares pesados
        self.check_middlewares()

        self.stdout.write('\n📊 DIAGNÓSTICO CONCLUÍDO')

    def test_basic_db_connection(self):
        """Testa conexão básica com timeout"""
        self.stdout.write('1️⃣ Testando conexão básica com banco...')

        def db_test():
            try:
                start_time = time.time()
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                elapsed = time.time() - start_time
                return elapsed, result
            except Exception as e:
                return None, str(e)

        # Executar com timeout de 5 segundos
        result = self.run_with_timeout(db_test, 5)

        if result is None:
            self.stdout.write('   🚨 CRÍTICO: Conexão DB travou (>5s)')
        elif isinstance(result[1], str):  # erro
            self.stdout.write(f'   ❌ ERRO: {result[1]}')
        else:
            elapsed, _ = result
            if elapsed > 2:
                self.stdout.write(f'   ⚠️ LENTO: {elapsed:.3f}s (normal: <0.1s)')
            else:
                self.stdout.write(f'   ✅ OK: {elapsed:.3f}s')

    def check_problematic_settings(self):
        """Verifica configurações que podem causar lentidão"""
        self.stdout.write('\n2️⃣ Verificando configurações problemáticas...')

        # DEBUG ativo
        if settings.DEBUG:
            self.stdout.write('   ⚠️ DEBUG=True (pode causar lentidão)')
        else:
            self.stdout.write('   ✅ DEBUG=False')

        # Verificar LOGGING
        if hasattr(settings, 'LOGGING'):
            logging_config = settings.LOGGING
            if 'django.db.backends' in str(logging_config):
                self.stdout.write('   ⚠️ Log de SQL ativo (pode causar lentidão)')
            else:
                self.stdout.write('   ✅ Log de SQL não detectado')

        # Verificar middlewares pesados
        middlewares = getattr(settings, 'MIDDLEWARE', [])
        heavy_middlewares = [
            'debug_toolbar',
            'silk',
            'django_extensions'
        ]

        for middleware in middlewares:
            for heavy in heavy_middlewares:
                if heavy in middleware.lower():
                    self.stdout.write(f'   ⚠️ Middleware pesado: {middleware}')
                    break

        # Verificar DATABASES
        db_config = settings.DATABASES.get('default', {})
        engine = db_config.get('ENGINE', '')

        if 'sqlite' in engine.lower():
            db_name = db_config.get('NAME', '')
            self.stdout.write(f'   📝 SQLite: {db_name}')

            # Verificar tamanho do arquivo SQLite
            try:
                import os
                if os.path.exists(db_name):
                    size_mb = os.path.getsize(db_name) / (1024 * 1024)
                    self.stdout.write(f'   📏 Tamanho DB: {size_mb:.2f}MB')
                    if size_mb > 100:
                        self.stdout.write('   ⚠️ DB grande para SQLite (considere PostgreSQL)')
            except:
                pass

    def test_individual_caches(self):
        """Testa cada cache individualmente"""
        self.stdout.write('\n3️⃣ Testando caches individuais...')

        cache_names = ['default', 'recommendations', 'google_books', 'image_proxy']

        for cache_name in cache_names:
            try:
                start_time = time.time()
                cache = caches[cache_name]

                # Teste simples com timeout
                def cache_test():
                    cache.set('perf_test', 'test_value', 10)
                    value = cache.get('perf_test')
                    cache.delete('perf_test')
                    return value

                result = self.run_with_timeout(cache_test, 3)
                elapsed = time.time() - start_time

                if result is None:
                    self.stdout.write(f'   🚨 {cache_name}: TRAVOU (>3s)')
                elif result == 'test_value':
                    if elapsed > 1:
                        self.stdout.write(f'   ⚠️ {cache_name}: LENTO ({elapsed:.3f}s)')
                    else:
                        self.stdout.write(f'   ✅ {cache_name}: OK ({elapsed:.3f}s)')
                else:
                    self.stdout.write(f'   ❌ {cache_name}: FALHOU')

            except Exception as e:
                self.stdout.write(f'   ❌ {cache_name}: ERRO - {str(e)[:50]}')

    def check_active_queries(self):
        """Verifica queries ativas e possíveis locks"""
        self.stdout.write('\n4️⃣ Verificando queries ativas...')

        try:
            # Para SQLite, verificar se há um arquivo .lock
            db_config = settings.DATABASES.get('default', {})
            if 'sqlite' in db_config.get('ENGINE', '').lower():
                db_name = db_config.get('NAME', '')
                lock_file = f"{db_name}-wal"

                try:
                    import os
                    if os.path.exists(lock_file):
                        lock_size = os.path.getsize(lock_file)
                        self.stdout.write(f'   📝 WAL file: {lock_size} bytes')
                        if lock_size > 1024 * 1024:  # 1MB
                            self.stdout.write('   ⚠️ WAL file grande (pode indicar transações longas)')
                    else:
                        self.stdout.write('   ✅ Nenhum WAL file detectado')
                except:
                    pass

            # Verificar queries registradas pelo Django
            if hasattr(connection, 'queries'):
                query_count = len(connection.queries)
                if query_count > 100:
                    self.stdout.write(f'   ⚠️ Muitas queries em memória: {query_count}')
                else:
                    self.stdout.write(f'   ✅ Queries em memória: {query_count}')

        except Exception as e:
            self.stdout.write(f'   ❌ Erro ao verificar queries: {e}')

    def test_model_imports(self):
        """Testa importação de modelos para detectar lentidão"""
        self.stdout.write('\n5️⃣ Testando importação de modelos...')

        models_to_test = [
            ('Book', 'cgbookstore.apps.core.models.book', 'Book'),
            ('User', 'django.contrib.auth', 'get_user_model'),
            ('UserBookShelf', 'cgbookstore.apps.core.models', 'UserBookShelf'),
        ]

        for model_name, module_path, class_name in models_to_test:
            start_time = time.time()

            try:
                def import_test():
                    if class_name == 'get_user_model':
                        from django.contrib.auth import get_user_model
                        model = get_user_model()
                    else:
                        module = __import__(module_path, fromlist=[class_name])
                        model = getattr(module, class_name)
                    return model

                result = self.run_with_timeout(import_test, 3)
                elapsed = time.time() - start_time

                if result is None:
                    self.stdout.write(f'   🚨 {model_name}: TRAVOU na importação')
                elif elapsed > 1:
                    self.stdout.write(f'   ⚠️ {model_name}: LENTO ({elapsed:.3f}s)')
                else:
                    self.stdout.write(f'   ✅ {model_name}: OK ({elapsed:.3f}s)')

            except Exception as e:
                self.stdout.write(f'   ❌ {model_name}: ERRO - {str(e)[:50]}')

    def check_middlewares(self):
        """Verifica middlewares que podem causar lentidão"""
        self.stdout.write('\n6️⃣ Verificando middlewares...')

        middlewares = getattr(settings, 'MIDDLEWARE', [])

        problematic_patterns = [
            ('debug_toolbar', 'Django Debug Toolbar'),
            ('silk', 'Django Silk'),
            ('django_extensions', 'Django Extensions'),
            ('corsheaders', 'CORS Headers'),
            ('whitenoise', 'WhiteNoise'),
        ]

        found_heavy = False
        for middleware in middlewares:
            for pattern, name in problematic_patterns:
                if pattern in middleware.lower():
                    self.stdout.write(f'   ⚠️ {name}: {middleware}')
                    found_heavy = True

        if not found_heavy:
            self.stdout.write('   ✅ Nenhum middleware pesado detectado')

        self.stdout.write(f'   📊 Total middlewares: {len(middlewares)}')

    def run_with_timeout(self, func, timeout_seconds):
        """Executa função com timeout"""
        result = [None]
        exception = [None]

        def target():
            try:
                result[0] = func()
            except Exception as e:
                exception[0] = e

        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout_seconds)

        if thread.is_alive():
            return None  # Timeout

        if exception[0]:
            raise exception[0]

        return result[0]
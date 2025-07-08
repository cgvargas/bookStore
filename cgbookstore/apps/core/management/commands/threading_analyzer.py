# cgbookstore/apps/core/management/commands/threading_analyzer.py

import os
import time
import signal
import threading
import glob
from django.core.management.base import BaseCommand
from django.conf import settings
from django.apps import apps


class Command(BaseCommand):
    help = 'Analisa problemas de threading, signals e StatReloader'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🧵 ANALISADOR DE THREADING E SIGNALS\n')
        )

        # 1. Analisar signals registrados
        self.analyze_registered_signals()

        # 2. Analisar StatReloader e arquivos monitorados
        self.analyze_statreloader()

        # 3. Analisar configurações de static files
        self.analyze_static_files()

        # 4. Verificar threads ativas
        self.analyze_active_threads()

        # 5. Testar performance de operações de arquivo
        self.test_file_operations()

        # 6. Analisar configurações problemáticas
        self.analyze_problematic_configs()

    def analyze_registered_signals(self):
        """Analisa signals registrados que podem causar problemas"""
        self.stdout.write('1️⃣ Analisando signals registrados...')

        try:
            import django.dispatch

            # Listar todos os signals
            signal_count = 0
            potential_problems = []

            # Verificar signals do Django
            from django.db.models.signals import (
                post_save, pre_save, post_delete, pre_delete,
                m2m_changed, pre_migrate, post_migrate
            )

            signal_types = [
                ('post_save', post_save),
                ('pre_save', pre_save),
                ('post_delete', post_delete),
                ('pre_delete', pre_delete),
                ('m2m_changed', m2m_changed),
                ('pre_migrate', pre_migrate),
                ('post_migrate', post_migrate),
            ]

            for signal_name, signal_obj in signal_types:
                receivers = getattr(signal_obj, 'receivers', [])
                receiver_count = len(receivers) if receivers else 0
                signal_count += receiver_count

                if receiver_count > 0:
                    self.stdout.write(f'   📡 {signal_name}: {receiver_count} receivers')

                    # Verificar se há receivers que podem ser problemáticos
                    for receiver in receivers:
                        try:
                            receiver_func = receiver[1]()  # WeakRef
                            if receiver_func:
                                func_name = getattr(receiver_func, '__name__', 'unknown')
                                module_name = getattr(receiver_func, '__module__', 'unknown')

                                # Verificar padrões problemáticos
                                if any(pattern in module_name.lower() for pattern in
                                       ['cache', 'image', 'google', 'api', 'request']):
                                    potential_problems.append(f'{signal_name}.{func_name} ({module_name})')

                        except:
                            continue

            self.stdout.write(f'   📊 Total de signals: {signal_count}')

            if potential_problems:
                self.stdout.write('   ⚠️ Signals potencialmente problemáticos:')
                for problem in potential_problems:
                    self.stdout.write(f'      - {problem}')
            else:
                self.stdout.write('   ✅ Nenhum signal problemático detectado')

        except Exception as e:
            self.stdout.write(f'   ❌ Erro ao analisar signals: {e}')

    def analyze_statreloader(self):
        """Analisa o StatReloader e arquivos monitorados"""
        self.stdout.write('\n2️⃣ Analisando StatReloader...')

        try:
            # Simular o que o StatReloader faz
            from django.utils.autoreload import StatReloader

            start_time = time.time()

            # Criar um StatReloader para testar
            reloader = StatReloader()

            # Verificar quantos arquivos ele monitora
            watched_files = set()

            # Simular descoberta de arquivos Python
            for app_config in apps.get_app_configs():
                app_path = app_config.path
                if os.path.exists(app_path):
                    for root, dirs, files in os.walk(app_path):
                        for file in files:
                            if file.endswith('.py'):
                                watched_files.add(os.path.join(root, file))

            # Adicionar arquivos do projeto principal
            base_dir = getattr(settings, 'BASE_DIR', os.getcwd())
            for root, dirs, files in os.walk(base_dir):
                # Pular diretórios grandes desnecessários
                dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.venv', '.venv1', 'node_modules']]

                for file in files:
                    if file.endswith('.py'):
                        watched_files.add(os.path.join(root, file))

            discovery_time = time.time() - start_time
            file_count = len(watched_files)

            self.stdout.write(f'   📁 Arquivos monitorados: {file_count}')
            self.stdout.write(f'   ⏱️ Tempo de descoberta: {discovery_time:.3f}s')

            if file_count > 1000:
                self.stdout.write('   🚨 MUITOS arquivos monitorados (pode causar lentidão)')
            elif file_count > 500:
                self.stdout.write('   ⚠️ Número alto de arquivos monitorados')
            else:
                self.stdout.write('   ✅ Número normal de arquivos')

            # Testar performance de stat() em alguns arquivos
            if watched_files:
                sample_files = list(watched_files)[:100]  # Testar uma amostra

                start_time = time.time()
                for filepath in sample_files:
                    try:
                        os.stat(filepath)
                    except:
                        continue
                stat_time = time.time() - start_time

                avg_stat_time = stat_time / len(sample_files)
                self.stdout.write(f'   📊 Tempo médio de stat(): {avg_stat_time * 1000:.1f}ms')

                if avg_stat_time > 0.01:  # 10ms por arquivo
                    self.stdout.write('   🚨 stat() muito lento (problema de I/O)')

        except Exception as e:
            self.stdout.write(f'   ❌ Erro ao analisar StatReloader: {e}')

    def analyze_static_files(self):
        """Analisa configurações de arquivos estáticos"""
        self.stdout.write('\n3️⃣ Analisando arquivos estáticos...')

        try:
            # Verificar STATICFILES_DIRS
            static_dirs = getattr(settings, 'STATICFILES_DIRS', [])
            static_root = getattr(settings, 'STATIC_ROOT', None)
            static_url = getattr(settings, 'STATIC_URL', '/static/')

            self.stdout.write(f'   📂 STATICFILES_DIRS: {len(static_dirs)} diretórios')

            total_static_files = 0
            for static_dir in static_dirs:
                if os.path.exists(static_dir):
                    start_time = time.time()
                    file_count = sum(len(files) for _, _, files in os.walk(static_dir))
                    scan_time = time.time() - start_time

                    total_static_files += file_count
                    self.stdout.write(f'      {static_dir}: {file_count} arquivos ({scan_time:.3f}s)')

                    if scan_time > 1.0:
                        self.stdout.write('      🚨 Diretório muito lento para escanear')
                else:
                    self.stdout.write(f'      {static_dir}: Não existe')

            # Verificar STATIC_ROOT
            if static_root and os.path.exists(static_root):
                start_time = time.time()
                static_root_files = sum(len(files) for _, _, files in os.walk(static_root))
                scan_time = time.time() - start_time

                self.stdout.write(f'   📁 STATIC_ROOT: {static_root_files} arquivos ({scan_time:.3f}s)')

                if scan_time > 2.0:
                    self.stdout.write('   🚨 STATIC_ROOT muito lento para escanear')

            self.stdout.write(f'   📊 Total arquivos estáticos: {total_static_files}')

            if total_static_files > 10000:
                self.stdout.write('   🚨 MUITOS arquivos estáticos (considere --nostatic)')
            elif total_static_files > 5000:
                self.stdout.write('   ⚠️ Muitos arquivos estáticos')
            else:
                self.stdout.write('   ✅ Quantidade normal de arquivos estáticos')

        except Exception as e:
            self.stdout.write(f'   ❌ Erro ao analisar static files: {e}')

    def analyze_active_threads(self):
        """Analisa threads ativas"""
        self.stdout.write('\n4️⃣ Analisando threads ativas...')

        try:
            active_threads = threading.active_count()
            self.stdout.write(f'   🧵 Threads ativas: {active_threads}')

            # Listar threads por nome
            for thread in threading.enumerate():
                thread_name = getattr(thread, 'name', 'unnamed')
                is_daemon = getattr(thread, 'daemon', False)
                is_alive = thread.is_alive()

                status = '✅' if is_alive else '❌'
                daemon_status = '(daemon)' if is_daemon else '(main)'

                self.stdout.write(f'   {status} {thread_name} {daemon_status}')

            if active_threads > 10:
                self.stdout.write('   ⚠️ Muitas threads ativas')
            else:
                self.stdout.write('   ✅ Número normal de threads')

        except Exception as e:
            self.stdout.write(f'   ❌ Erro ao analisar threads: {e}')

    def test_file_operations(self):
        """Testa performance de operações de arquivo"""
        self.stdout.write('\n5️⃣ Testando performance de I/O...')

        try:
            base_dir = getattr(settings, 'BASE_DIR', os.getcwd())

            # Teste 1: os.walk no diretório base
            start_time = time.time()
            file_count = 0
            for root, dirs, files in os.walk(base_dir):
                # Pular diretórios grandes
                dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.venv', '.venv1', 'node_modules']]
                file_count += len(files)

                # Limite para evitar travamento
                if file_count > 10000:
                    break

            walk_time = time.time() - start_time
            self.stdout.write(f'   📁 os.walk(): {file_count} arquivos em {walk_time:.3f}s')

            if walk_time > 5.0:
                self.stdout.write('   🚨 os.walk() MUITO lento')
            elif walk_time > 1.0:
                self.stdout.write('   ⚠️ os.walk() lento')
            else:
                self.stdout.write('   ✅ os.walk() normal')

            # Teste 2: glob para arquivos Python
            start_time = time.time()
            python_files = glob.glob(os.path.join(base_dir, '**', '*.py'), recursive=True)
            glob_time = time.time() - start_time

            self.stdout.write(f'   🐍 glob *.py: {len(python_files)} arquivos em {glob_time:.3f}s')

            if glob_time > 3.0:
                self.stdout.write('   🚨 glob MUITO lento')
            elif glob_time > 1.0:
                self.stdout.write('   ⚠️ glob lento')
            else:
                self.stdout.write('   ✅ glob normal')

        except Exception as e:
            self.stdout.write(f'   ❌ Erro ao testar I/O: {e}')

    def analyze_problematic_configs(self):
        """Analisa configurações que podem causar problemas"""
        self.stdout.write('\n6️⃣ Analisando configurações problemáticas...')

        problems_found = []

        # Verificar DEBUG
        if settings.DEBUG:
            problems_found.append('DEBUG=True (pode causar lentidão)')

        # Verificar LOGGING
        if hasattr(settings, 'LOGGING'):
            logging_config = settings.LOGGING
            if any('django.db.backends' in str(handler) for handler in logging_config.get('loggers', {}).values()):
                problems_found.append('Log de queries SQL ativo')

        # Verificar middlewares pesados
        middleware = getattr(settings, 'MIDDLEWARE', [])
        heavy_middleware = [
            'debug_toolbar', 'silk', 'django_extensions',
            'corsheaders', 'whitenoise'
        ]

        for mw in middleware:
            for heavy in heavy_middleware:
                if heavy in mw.lower():
                    problems_found.append(f'Middleware pesado: {mw}')

        # Verificar INSTALLED_APPS pesadas
        installed_apps = getattr(settings, 'INSTALLED_APPS', [])
        heavy_apps = [
            'debug_toolbar', 'django_extensions', 'silk',
            'rest_framework', 'channels', 'celery'
        ]

        for app in installed_apps:
            for heavy in heavy_apps:
                if heavy in app:
                    problems_found.append(f'App pesada: {app}')

        # Verificar cache backends
        caches = getattr(settings, 'CACHES', {})
        for cache_name, cache_config in caches.items():
            backend = cache_config.get('BACKEND', '')
            if 'DatabaseCache' in backend:
                problems_found.append(f'Cache em banco: {cache_name}')

        # Mostrar resultados
        if problems_found:
            self.stdout.write('   ⚠️ Problemas encontrados:')
            for problem in problems_found:
                self.stdout.write(f'      - {problem}')
        else:
            self.stdout.write('   ✅ Nenhuma configuração problemática detectada')

        # Recomendações finais
        self.stdout.write('\n💡 RECOMENDAÇÕES FINAIS:')

        if any('DEBUG' in p for p in problems_found):
            self.stdout.write('   🔧 Para produção: DEBUG=False')

        if any('Middleware' in p for p in problems_found):
            self.stdout.write('   🔧 Remover middlewares de desenvolvimento')

        if any('App pesada' in p for p in problems_found):
            self.stdout.write('   🔧 Remover apps de desenvolvimento desnecessárias')

        self.stdout.write('\n🚀 Testes para fazer:')
        self.stdout.write('   python manage.py runserver --noreload')
        self.stdout.write('   python manage.py runserver --nostatic')
        self.stdout.write('   DEBUG=False python manage.py runserver')
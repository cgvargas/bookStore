# cgbookstore/apps/core/management/commands/startup_profiler.py

import time
import sys
import importlib
from django.core.management.base import BaseCommand
from django.conf import settings
from django.apps import apps


class Command(BaseCommand):
    help = 'Analisa o tempo de inicialização de cada componente do Django'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('⏱️ PROFILER DE STARTUP DO DJANGO\n')
        )

        total_start = time.time()

        # 1. Testar carregamento de apps
        self.profile_apps_loading()

        # 2. Testar importação de URLs
        self.profile_urls_loading()

        # 3. Testar inicialização de signals
        self.profile_signals()

        # 4. Testar importações específicas pesadas
        self.profile_heavy_imports()

        # 5. Testar configurações que podem causar lentidão
        self.profile_settings_impact()

        # 6. Simular processo completo do runserver
        self.simulate_runserver_startup()

        total_time = time.time() - total_start
        self.stdout.write(f'\n⏱️ TEMPO TOTAL DO PROFILER: {total_time:.3f}s')

    def profile_apps_loading(self):
        """Perfila o carregamento de cada app"""
        self.stdout.write('1️⃣ Analisando carregamento de apps...')

        app_times = {}

        for app_config in apps.get_app_configs():
            app_name = app_config.name

            start_time = time.time()
            try:
                # Tentar importar o módulo da app
                importlib.import_module(app_name)
                elapsed = time.time() - start_time
                app_times[app_name] = elapsed

                if elapsed > 0.1:
                    self.stdout.write(f'   ⚠️ {app_name}: {elapsed:.3f}s')
                elif elapsed > 0.05:
                    self.stdout.write(f'   🟡 {app_name}: {elapsed:.3f}s')
                else:
                    self.stdout.write(f'   ✅ {app_name}: {elapsed:.3f}s')

            except Exception as e:
                self.stdout.write(f'   ❌ {app_name}: ERRO - {str(e)[:50]}')

        # Mostrar os 3 apps mais lentos
        if app_times:
            slowest = sorted(app_times.items(), key=lambda x: x[1], reverse=True)[:3]
            self.stdout.write('\n   🐌 Apps mais lentas:')
            for app_name, time_taken in slowest:
                self.stdout.write(f'      {app_name}: {time_taken:.3f}s')

    def profile_urls_loading(self):
        """Perfila o carregamento de URLs"""
        self.stdout.write('\n2️⃣ Analisando carregamento de URLs...')

        try:
            start_time = time.time()

            # Importar URLconf principal
            root_urlconf = settings.ROOT_URLCONF
            importlib.import_module(root_urlconf)

            elapsed = time.time() - start_time

            if elapsed > 0.5:
                self.stdout.write(f'   ⚠️ URLs principais: {elapsed:.3f}s (LENTO)')
            else:
                self.stdout.write(f'   ✅ URLs principais: {elapsed:.3f}s')

            # Testar URLs específicas das apps
            app_urls = [
                ('cgbookstore.apps.core.urls', 'Core URLs'),
                ('cgbookstore.apps.core.urls_author', 'Author URLs'),
                ('cgbookstore.apps.chatbot_literario.urls', 'Chatbot URLs'),
                ('cgbookstore.apps.core.recommendations.urls', 'Recommendations URLs'),
            ]

            for url_module, description in app_urls:
                try:
                    start_time = time.time()
                    importlib.import_module(url_module)
                    elapsed = time.time() - start_time

                    if elapsed > 0.1:
                        self.stdout.write(f'   ⚠️ {description}: {elapsed:.3f}s')
                    else:
                        self.stdout.write(f'   ✅ {description}: {elapsed:.3f}s')

                except ImportError:
                    self.stdout.write(f'   ❌ {description}: Não encontrado')
                except Exception as e:
                    self.stdout.write(f'   ❌ {description}: ERRO - {str(e)[:30]}')

        except Exception as e:
            self.stdout.write(f'   ❌ Erro ao carregar URLs: {e}')

    def profile_signals(self):
        """Perfila a inicialização de signals"""
        self.stdout.write('\n3️⃣ Analisando inicialização de signals...')

        signals_modules = [
            ('cgbookstore.apps.core.signals', 'Core Signals'),
            ('cgbookstore.apps.chatbot_literario.signals', 'Chatbot Signals'),
        ]

        for signal_module, description in signals_modules:
            try:
                start_time = time.time()
                importlib.import_module(signal_module)
                elapsed = time.time() - start_time

                if elapsed > 0.1:
                    self.stdout.write(f'   ⚠️ {description}: {elapsed:.3f}s')
                else:
                    self.stdout.write(f'   ✅ {description}: {elapsed:.3f}s')

            except ImportError:
                self.stdout.write(f'   ❌ {description}: Não encontrado')
            except Exception as e:
                self.stdout.write(f'   ❌ {description}: ERRO - {str(e)[:30]}')

    def profile_heavy_imports(self):
        """Testa importações que podem ser pesadas"""
        self.stdout.write('\n4️⃣ Analisando importações pesadas...')

        heavy_imports = [
            ('requests', 'Requests library'),
            ('pandas', 'Pandas (se usado)'),
            ('numpy', 'NumPy (se usado)'),
            ('PIL', 'Pillow'),
            ('redis', 'Redis client'),
            ('django.contrib.admin', 'Django Admin'),
            ('django.contrib.staticfiles', 'Static Files'),
            ('cgbookstore.apps.core.services.google_books_service', 'Google Books Service'),
            ('cgbookstore.apps.core.recommendations.engine', 'Recommendation Engine'),
        ]

        for module_name, description in heavy_imports:
            try:
                start_time = time.time()
                importlib.import_module(module_name)
                elapsed = time.time() - start_time

                if elapsed > 0.5:
                    self.stdout.write(f'   🚨 {description}: {elapsed:.3f}s (MUITO LENTO)')
                elif elapsed > 0.1:
                    self.stdout.write(f'   ⚠️ {description}: {elapsed:.3f}s')
                else:
                    self.stdout.write(f'   ✅ {description}: {elapsed:.3f}s')

            except ImportError:
                self.stdout.write(f'   ➖ {description}: Não instalado')
            except Exception as e:
                self.stdout.write(f'   ❌ {description}: ERRO - {str(e)[:30]}')

    def profile_settings_impact(self):
        """Analisa impacto das configurações"""
        self.stdout.write('\n5️⃣ Analisando impacto das configurações...')

        # Verificar INSTALLED_APPS
        installed_apps = getattr(settings, 'INSTALLED_APPS', [])
        app_count = len(installed_apps)

        if app_count > 20:
            self.stdout.write(f'   ⚠️ Muitas apps instaladas: {app_count}')
        else:
            self.stdout.write(f'   ✅ Apps instaladas: {app_count}')

        # Verificar apps de terceiros pesadas
        heavy_third_party = [
            'debug_toolbar',
            'django_extensions',
            'silk',
            'rest_framework',
            'celery',
            'channels',
        ]

        found_heavy = []
        for app in installed_apps:
            for heavy in heavy_third_party:
                if heavy in app:
                    found_heavy.append(app)

        if found_heavy:
            self.stdout.write('   ⚠️ Apps de terceiros pesadas encontradas:')
            for app in found_heavy:
                self.stdout.write(f'      - {app}')
        else:
            self.stdout.write('   ✅ Nenhuma app de terceiros pesada detectada')

        # Verificar middleware
        middleware = getattr(settings, 'MIDDLEWARE', [])
        self.stdout.write(f'   📊 Middlewares configurados: {len(middleware)}')

        # Verificar templates
        templates = getattr(settings, 'TEMPLATES', [])
        if templates:
            template_dirs = templates[0].get('DIRS', [])
            self.stdout.write(f'   📁 Diretórios de templates: {len(template_dirs)}')

    def simulate_runserver_startup(self):
        """Simula o processo completo de startup do runserver"""
        self.stdout.write('\n6️⃣ Simulando startup completo do runserver...')

        steps = [
            ('Importar Django', lambda: importlib.import_module('django')),
            ('Configurar settings', lambda: None),  # Já configurado
            ('Inicializar apps', lambda: apps.populate(settings.INSTALLED_APPS) if not apps.ready else None),
            ('Carregar URLs', lambda: importlib.import_module(settings.ROOT_URLCONF)),
            ('Verificar migrações', self.quick_migration_check),
            ('Inicializar static files', self.check_static_files),
        ]

        total_simulation_time = 0

        for step_name, step_func in steps:
            try:
                start_time = time.time()
                step_func()
                elapsed = time.time() - start_time
                total_simulation_time += elapsed

                if elapsed > 1.0:
                    self.stdout.write(f'   🚨 {step_name}: {elapsed:.3f}s (MUITO LENTO)')
                elif elapsed > 0.2:
                    self.stdout.write(f'   ⚠️ {step_name}: {elapsed:.3f}s')
                else:
                    self.stdout.write(f'   ✅ {step_name}: {elapsed:.3f}s')

            except Exception as e:
                self.stdout.write(f'   ❌ {step_name}: ERRO - {str(e)[:40]}')

        self.stdout.write(f'\n   ⏱️ Tempo total simulado: {total_simulation_time:.3f}s')

    def quick_migration_check(self):
        """Verificação rápida de migrações sem executar"""
        try:
            from django.core.management import execute_from_command_line
            from django.db.migrations.executor import MigrationExecutor
            from django.db import connections

            connection = connections['default']
            executor = MigrationExecutor(connection)

            # Apenas verificar se há migrações pendentes (sem aplicar)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())

            if plan:
                self.stdout.write(f'      ⚠️ {len(plan)} migrações pendentes detectadas')

        except Exception:
            # Se der erro, ignora - é só uma verificação
            pass

    def check_static_files(self):
        """Verificação básica de arquivos estáticos"""
        try:
            import os
            static_root = getattr(settings, 'STATIC_ROOT', None)
            static_url = getattr(settings, 'STATIC_URL', '/static/')

            if static_root and os.path.exists(static_root):
                file_count = len([f for f in os.listdir(static_root) if os.path.isfile(os.path.join(static_root, f))])
                if file_count > 1000:
                    self.stdout.write(f'      ⚠️ Muitos arquivos estáticos: {file_count}')

        except Exception:
            # Se der erro, ignora
            pass
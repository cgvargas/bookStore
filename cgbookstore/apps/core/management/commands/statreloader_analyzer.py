# cgbookstore/apps/core/management/commands/statreloader_analyzer.py

import os
import time
import sys
from pathlib import Path
from collections import defaultdict
from django.core.management.base import BaseCommand
from django.conf import settings
from django.apps import apps


class Command(BaseCommand):
    help = 'Analisa especificamente o StatReloader para identificar lentidão'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔍 ANALISADOR ESPECÍFICO DO STATRELOADER\n')
        )

        # 1. Simular descoberta de arquivos do StatReloader
        self.analyze_file_discovery()

        # 2. Testar performance de stat() em lote
        self.test_stat_performance()

        # 3. Analisar diretórios problemáticos
        self.analyze_problematic_directories()

        # 4. Verificar configurações que afetam o StatReloader
        self.analyze_reloader_settings()

        # 5. Sugerir otimizações
        self.suggest_optimizations()

    def analyze_file_discovery(self):
        """Simula exatamente o que o StatReloader faz para descobrir arquivos"""
        self.stdout.write('1️⃣ Simulando descoberta de arquivos do StatReloader...')

        total_start = time.time()

        # Arquivos que o StatReloader monitora
        watched_files = set()
        directory_stats = {}

        # 1. Arquivos Python do próprio Django
        self.stdout.write('   📁 Descobrindo arquivos do Django...')
        start_time = time.time()
        try:
            import django
            django_dir = Path(django.__file__).parent
            django_files = list(django_dir.rglob('*.py'))
            watched_files.update(str(f) for f in django_files)
            directory_stats['Django Core'] = {
                'files': len(django_files),
                'time': time.time() - start_time
            }
        except Exception as e:
            self.stdout.write(f'      ❌ Erro: {e}')

        # 2. Arquivos das apps instaladas
        self.stdout.write('   📱 Descobrindo arquivos das apps...')
        for app_config in apps.get_app_configs():
            start_time = time.time()
            app_name = app_config.name
            app_path = Path(app_config.path)

            if app_path.exists():
                app_files = list(app_path.rglob('*.py'))
                watched_files.update(str(f) for f in app_files)

                elapsed = time.time() - start_time
                directory_stats[app_name] = {
                    'files': len(app_files),
                    'time': elapsed
                }

                if elapsed > 0.5:
                    self.stdout.write(f'      🚨 {app_name}: {len(app_files)} arquivos em {elapsed:.3f}s')
                elif elapsed > 0.1:
                    self.stdout.write(f'      ⚠️ {app_name}: {len(app_files)} arquivos em {elapsed:.3f}s')
                else:
                    self.stdout.write(f'      ✅ {app_name}: {len(app_files)} arquivos em {elapsed:.3f}s')
            else:
                self.stdout.write(f'      ❓ {app_name}: Diretório não existe')

        # 3. Arquivos do projeto principal (mais crítico)
        self.stdout.write('   🏠 Descobrindo arquivos do projeto...')
        start_time = time.time()
        base_dir = Path(settings.BASE_DIR)

        # Simular o que o StatReloader faz - varrer recursivamente
        project_files = []
        excluded_dirs = {'.git', '__pycache__', '.venv', '.venv1', 'node_modules', '.pytest_cache', '.idea'}

        for root, dirs, files in os.walk(base_dir):
            # Remover diretórios excluídos da busca
            dirs[:] = [d for d in dirs if d not in excluded_dirs]

            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    project_files.append(file_path)
                    watched_files.add(file_path)

        project_discovery_time = time.time() - start_time
        directory_stats['Projeto Principal'] = {
            'files': len(project_files),
            'time': project_discovery_time
        }

        if project_discovery_time > 2.0:
            self.stdout.write(
                f'      🚨 Projeto Principal: {len(project_files)} arquivos em {project_discovery_time:.3f}s')
        else:
            self.stdout.write(
                f'      ✅ Projeto Principal: {len(project_files)} arquivos em {project_discovery_time:.3f}s')

        # 4. Arquivos de configuração e manage.py
        self.stdout.write('   ⚙️ Descobrindo arquivos de configuração...')
        start_time = time.time()
        config_files = [
            base_dir / 'manage.py',
            base_dir / 'cgbookstore' / 'config' / 'settings.py',
            base_dir / 'cgbookstore' / 'config' / 'urls.py',
        ]

        config_count = 0
        for config_file in config_files:
            if config_file.exists():
                watched_files.add(str(config_file))
                config_count += 1

        config_discovery_time = time.time() - start_time
        directory_stats['Configuração'] = {
            'files': config_count,
            'time': config_discovery_time
        }

        total_discovery_time = time.time() - total_start

        # Mostrar resumo
        self.stdout.write(f'\n   📊 RESUMO DA DESCOBERTA:')
        self.stdout.write(f'      Total de arquivos: {len(watched_files)}')
        self.stdout.write(f'      Tempo total: {total_discovery_time:.3f}s')

        # Mostrar os mais lentos
        slow_discoveries = [(name, stats) for name, stats in directory_stats.items() if stats['time'] > 0.1]
        if slow_discoveries:
            self.stdout.write(f'\n   🐌 Descobertas mais lentas:')
            for name, stats in sorted(slow_discoveries, key=lambda x: x[1]['time'], reverse=True):
                self.stdout.write(f'      {name}: {stats["files"]} arquivos em {stats["time"]:.3f}s')

        return watched_files

    def test_stat_performance(self):
        """Testa performance de os.stat() em lote"""
        self.stdout.write('\n2️⃣ Testando performance de os.stat()...')

        # Obter lista de arquivos Python no projeto
        base_dir = Path(settings.BASE_DIR)
        python_files = []

        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.venv', '.venv1', 'node_modules'}]
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))

        if not python_files:
            self.stdout.write('   ❌ Nenhum arquivo Python encontrado')
            return

        # Testar os.stat() em lotes
        batch_sizes = [10, 50, 100, min(200, len(python_files))]

        for batch_size in batch_sizes:
            if batch_size > len(python_files):
                continue

            sample_files = python_files[:batch_size]

            start_time = time.time()
            successful_stats = 0
            failed_stats = 0

            for filepath in sample_files:
                try:
                    os.stat(filepath)
                    successful_stats += 1
                except Exception:
                    failed_stats += 1

            elapsed = time.time() - start_time
            avg_time = elapsed / batch_size

            if avg_time > 0.01:  # Mais de 10ms por arquivo
                self.stdout.write(
                    f'   🚨 {batch_size} arquivos: {elapsed:.3f}s (média: {avg_time * 1000:.1f}ms/arquivo)')
            elif avg_time > 0.005:  # Mais de 5ms por arquivo
                self.stdout.write(
                    f'   ⚠️ {batch_size} arquivos: {elapsed:.3f}s (média: {avg_time * 1000:.1f}ms/arquivo)')
            else:
                self.stdout.write(
                    f'   ✅ {batch_size} arquivos: {elapsed:.3f}s (média: {avg_time * 1000:.1f}ms/arquivo)')

            if failed_stats > 0:
                self.stdout.write(f'      ⚠️ {failed_stats} arquivos falharam no stat()')

    def analyze_problematic_directories(self):
        """Analisa diretórios que podem estar causando lentidão"""
        self.stdout.write('\n3️⃣ Analisando diretórios problemáticos...')

        base_dir = Path(settings.BASE_DIR)

        # Diretórios que podem causar problemas
        potentially_large_dirs = [
            base_dir / '.git',
            base_dir / 'node_modules',
            base_dir / '.venv',
            base_dir / '.venv1',
            base_dir / '__pycache__',
            base_dir / '.pytest_cache',
            base_dir / '.idea',
            base_dir / 'staticfiles',
            base_dir / 'media',
        ]

        for directory in potentially_large_dirs:
            if directory.exists():
                start_time = time.time()

                try:
                    # Contar arquivos (com limite para evitar travamento)
                    file_count = 0
                    dir_size = 0
                    max_files = 1000  # Limite para evitar travamento

                    for root, dirs, files in os.walk(directory):
                        file_count += len(files)

                        # Calcular tamanho aproximado
                        for file in files[:10]:  # Amostra de 10 arquivos por diretório
                            try:
                                file_path = os.path.join(root, file)
                                dir_size += os.path.getsize(file_path)
                            except:
                                continue

                        if file_count > max_files:
                            break

                    elapsed = time.time() - start_time
                    size_mb = dir_size / (1024 * 1024)

                    if elapsed > 1.0:
                        self.stdout.write(
                            f'   🚨 {directory.name}: {file_count}+ arquivos, ~{size_mb:.1f}MB ({elapsed:.3f}s)')
                        self.stdout.write(f'      ⚠️ Este diretório pode estar sendo monitorado desnecessariamente!')
                    elif elapsed > 0.5:
                        self.stdout.write(
                            f'   ⚠️ {directory.name}: {file_count} arquivos, ~{size_mb:.1f}MB ({elapsed:.3f}s)')
                    else:
                        self.stdout.write(
                            f'   ✅ {directory.name}: {file_count} arquivos, ~{size_mb:.1f}MB ({elapsed:.3f}s)')

                except Exception as e:
                    self.stdout.write(f'   ❌ {directory.name}: Erro ao analisar - {e}')
            else:
                self.stdout.write(f'   ➖ {directory.name}: Não existe')

    def analyze_reloader_settings(self):
        """Analisa configurações que afetam o reloader"""
        self.stdout.write('\n4️⃣ Analisando configurações do reloader...')

        # Verificar configurações relacionadas
        debug_status = getattr(settings, 'DEBUG', False)
        use_tz = getattr(settings, 'USE_TZ', False)

        self.stdout.write(f'   📊 DEBUG: {debug_status}')
        self.stdout.write(f'   🌍 USE_TZ: {use_tz}')

        # Verificar se há arquivos de configuração que mudam frequentemente
        config_files = [
            Path(settings.BASE_DIR) / 'cgbookstore' / 'config' / 'settings.py',
            Path(settings.BASE_DIR) / '.env.dev',
            Path(settings.BASE_DIR.parent) / '.env.dev',
        ]

        self.stdout.write('\n   📄 Arquivos de configuração:')
        for config_file in config_files:
            if config_file.exists():
                try:
                    stat_info = config_file.stat()
                    size_kb = stat_info.st_size / 1024
                    mtime = stat_info.st_mtime

                    self.stdout.write(f'      ✅ {config_file.name}: {size_kb:.1f}KB')

                    if size_kb > 100:  # Mais de 100KB
                        self.stdout.write(f'         ⚠️ Arquivo grande para configuração')

                except Exception as e:
                    self.stdout.write(f'      ❌ {config_file.name}: Erro - {e}')
            else:
                self.stdout.write(f'      ➖ {config_file.name}: Não encontrado')

    def suggest_optimizations(self):
        """Sugere otimizações baseadas na análise"""
        self.stdout.write('\n5️⃣ Sugestões de otimização...')

        self.stdout.write('\n   🚀 OTIMIZAÇÕES RECOMENDADAS:')

        # Verificar se .git existe
        base_dir = Path(settings.BASE_DIR)
        if (base_dir / '.git').exists():
            self.stdout.write('   📁 Criar .gitignore mais específico:')
            self.stdout.write('      - Excluir .venv*/ do monitoramento')
            self.stdout.write('      - Excluir __pycache__/ recursivamente')
            self.stdout.write('      - Excluir .pytest_cache/')

        # Verificar se há muitos arquivos estáticos
        static_dirs = getattr(settings, 'STATICFILES_DIRS', [])
        if static_dirs:
            self.stdout.write('   📂 Para desenvolvimento:')
            self.stdout.write('      - Usar --nostatic quando não precisar de CSS/JS')
            self.stdout.write('      - Considerar servir static files externamente')

        self.stdout.write('\n   ⚡ COMANDOS PARA TESTAR:')
        self.stdout.write('      python manage.py runserver --noreload  # Mais rápido')
        self.stdout.write('      python manage.py runserver --nostatic  # Sem static files')

        self.stdout.write('\n   🔧 CONFIGURAÇÕES RECOMENDADAS:')
        self.stdout.write('      - Mover .venv para fora do projeto')
        self.stdout.write('      - Usar SSD se possível (melhora I/O)')
        self.stdout.write('      - Considerar usar --noreload durante desenvolvimento')

        self.stdout.write('\n   📋 PARA PRODUÇÃO:')
        self.stdout.write('      - DEBUG=False')
        self.stdout.write('      - Usar servidor WSGI (não runserver)')
        self.stdout.write('      - Servir static files via nginx/apache')
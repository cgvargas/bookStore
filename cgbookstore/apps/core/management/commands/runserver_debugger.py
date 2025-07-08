# cgbookstore/apps/core/management/commands/runserver_debugger.py

import os
import sys
import time
import threading
import traceback
from io import StringIO
from django.core.management.base import BaseCommand
from django.core.management import execute_from_command_line
from django.conf import settings


class RunserverDebugger:
    """Intercepta e monitora o processo do runserver"""

    def __init__(self, stdout):
        self.stdout = stdout
        self.start_time = time.time()
        self.checkpoints = []
        self.io_operations = []
        self.slow_operations = []

    def checkpoint(self, name):
        """Marca um checkpoint com timestamp"""
        current_time = time.time()
        elapsed = current_time - self.start_time
        self.checkpoints.append((name, elapsed))

        if elapsed > 0.5:  # Mais de 500ms
            self.stdout.write(f'   🚨 {name}: {elapsed:.3f}s (LENTO)')
        elif elapsed > 0.1:  # Mais de 100ms
            self.stdout.write(f'   ⚠️ {name}: {elapsed:.3f}s')
        else:
            self.stdout.write(f'   ✅ {name}: {elapsed:.3f}s')

    def monitor_file_operations(self):
        """Monitora operações de arquivo usando monkey patching"""
        original_open = open
        original_listdir = os.listdir
        original_walk = os.walk
        original_stat = os.stat

        def tracked_open(*args, **kwargs):
            start = time.time()
            result = original_open(*args, **kwargs)
            elapsed = time.time() - start

            if elapsed > 0.1:
                filename = str(args[0]) if args else 'unknown'
                self.io_operations.append(('open', filename, elapsed))

            return result

        def tracked_listdir(*args, **kwargs):
            start = time.time()
            result = original_listdir(*args, **kwargs)
            elapsed = time.time() - start

            if elapsed > 0.1:
                dirname = str(args[0]) if args else 'unknown'
                self.io_operations.append(('listdir', dirname, elapsed))

            return result

        def tracked_walk(*args, **kwargs):
            start = time.time()
            result = list(original_walk(*args, **kwargs))
            elapsed = time.time() - start

            if elapsed > 0.1:
                dirname = str(args[0]) if args else 'unknown'
                self.io_operations.append(('walk', dirname, elapsed))

            return result

        def tracked_stat(*args, **kwargs):
            start = time.time()
            result = original_stat(*args, **kwargs)
            elapsed = time.time() - start

            if elapsed > 0.05:
                filename = str(args[0]) if args else 'unknown'
                self.io_operations.append(('stat', filename, elapsed))

            return result

        # Aplicar monkey patches
        __builtins__['open'] = tracked_open
        os.listdir = tracked_listdir
        os.walk = tracked_walk
        os.stat = tracked_stat

        return original_open, original_listdir, original_walk, original_stat


class Command(BaseCommand):
    help = 'Debugger profundo do processo runserver para identificar lentidão'

    def add_arguments(self, parser):
        parser.add_argument(
            '--port',
            type=str,
            default='8000',
            help='Porta para o servidor (padrão: 8000)'
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=30,
            help='Timeout para detectar travamento (padrão: 30s)'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔍 DEBUGGER PROFUNDO DO RUNSERVER\n')
        )

        debugger = RunserverDebugger(self.stdout)
        port = options['port']
        timeout = options['timeout']

        # 1. Preparar monitoramento
        self.stdout.write('1️⃣ Preparando monitoramento...')
        debugger.checkpoint('Início do debug')

        # 2. Interceptar operações de arquivo
        self.stdout.write('\n2️⃣ Ativando monitoramento de I/O...')
        original_funcs = debugger.monitor_file_operations()
        debugger.checkpoint('I/O monitoring ativo')

        # 3. Interceptar o runserver com timeout
        self.stdout.write(f'\n3️⃣ Iniciando runserver na porta {port} com timeout de {timeout}s...')

        # Usar thread para executar runserver com timeout
        runserver_thread = threading.Thread(
            target=self.run_server_with_debug,
            args=(debugger, port)
        )
        runserver_thread.daemon = True
        runserver_thread.start()

        # Aguardar com timeout
        runserver_thread.join(timeout)

        if runserver_thread.is_alive():
            self.stdout.write(
                self.style.ERROR(f'\n🚨 RUNSERVER TRAVOU após {timeout}s!')
            )
            self.stdout.write('⚠️ Processo ainda está rodando em background...')
        else:
            self.stdout.write('\n✅ Runserver iniciou normalmente.')

        # 4. Analisar resultados
        self.analyze_results(debugger)

        # 5. Restaurar funções originais
        __builtins__['open'] = original_funcs[0]
        os.listdir = original_funcs[1]
        os.walk = original_funcs[2]
        os.stat = original_funcs[3]

    def run_server_with_debug(self, debugger, port):
        """Executa o runserver com debug detalhado"""
        try:
            debugger.checkpoint('Antes de importar runserver command')

            # Importar comando runserver
            from django.core.management.commands.runserver import Command as RunserverCommand
            debugger.checkpoint('Runserver command importado')

            # Interceptar métodos do runserver
            original_command = RunserverCommand()
            self.intercept_runserver_methods(original_command, debugger)

            debugger.checkpoint('Métodos interceptados')

            # Executar runserver
            debugger.checkpoint('Iniciando execução do runserver')

            # Simular argumentos do runserver
            sys.argv = ['manage.py', 'runserver', f'127.0.0.1:{port}']

            # Capturar stdout para evitar spam
            old_stdout = sys.stdout
            sys.stdout = StringIO()

            try:
                original_command.run_from_argv(['manage.py', 'runserver', f'127.0.0.1:{port}'])
            finally:
                sys.stdout = old_stdout

            debugger.checkpoint('Runserver executado')

        except Exception as e:
            debugger.checkpoint(f'ERRO no runserver: {str(e)[:50]}')
            # Capturar traceback completo
            tb = traceback.format_exc()
            debugger.slow_operations.append(('runserver_error', str(e), tb))

    def intercept_runserver_methods(self, runserver_command, debugger):
        """Intercepta métodos específicos do runserver"""

        # Interceptar inner_run (método principal)
        original_inner_run = runserver_command.inner_run

        def debug_inner_run(*args, **kwargs):
            debugger.checkpoint('inner_run iniciado')

            # Interceptar get_handler
            self.intercept_get_handler(runserver_command, debugger)

            result = original_inner_run(*args, **kwargs)
            debugger.checkpoint('inner_run concluído')
            return result

        runserver_command.inner_run = debug_inner_run

        # Interceptar check_migrations
        original_check_migrations = getattr(runserver_command, 'check_migrations', None)
        if original_check_migrations:
            def debug_check_migrations(*args, **kwargs):
                debugger.checkpoint('check_migrations iniciado')
                result = original_check_migrations(*args, **kwargs)
                debugger.checkpoint('check_migrations concluído')
                return result

            runserver_command.check_migrations = debug_check_migrations

    def intercept_get_handler(self, runserver_command, debugger):
        """Intercepta o carregamento do handler WSGI"""
        original_get_handler = runserver_command.get_handler

        def debug_get_handler(*args, **kwargs):
            debugger.checkpoint('get_handler iniciado')

            # Aqui é onde o Django carrega todas as URLs e inicializa tudo
            result = original_get_handler(*args, **kwargs)

            debugger.checkpoint('get_handler concluído')
            return result

        runserver_command.get_handler = debug_get_handler

    def analyze_results(self, debugger):
        """Analisa os resultados do debug"""
        self.stdout.write('\n📊 ANÁLISE DOS RESULTADOS:\n')

        # Analisar checkpoints
        self.stdout.write('⏱️ Checkpoints temporais:')
        total_time = 0
        prev_time = 0

        for name, elapsed in debugger.checkpoints:
            step_time = elapsed - prev_time
            total_time = elapsed

            if step_time > 1.0:
                self.stdout.write(f'   🚨 {name}: +{step_time:.3f}s (total: {elapsed:.3f}s)')
            elif step_time > 0.2:
                self.stdout.write(f'   ⚠️ {name}: +{step_time:.3f}s (total: {elapsed:.3f}s)')
            else:
                self.stdout.write(f'   ✅ {name}: +{step_time:.3f}s (total: {elapsed:.3f}s)')

            prev_time = elapsed

        self.stdout.write(f'\n   ⏱️ TEMPO TOTAL: {total_time:.3f}s')

        # Analisar operações de I/O lentas
        if debugger.io_operations:
            self.stdout.write('\n📁 Operações de I/O lentas detectadas:')

            # Agrupar por tipo
            by_type = {}
            for op_type, path, duration in debugger.io_operations:
                if op_type not in by_type:
                    by_type[op_type] = []
                by_type[op_type].append((path, duration))

            for op_type, operations in by_type.items():
                self.stdout.write(f'\n   📂 {op_type.upper()}:')

                # Mostrar as 5 mais lentas
                operations.sort(key=lambda x: x[1], reverse=True)
                for path, duration in operations[:5]:
                    # Encurtar path se muito longo
                    display_path = path if len(path) < 60 else f"...{path[-57:]}"
                    self.stdout.write(f'      🐌 {display_path}: {duration:.3f}s')

                if len(operations) > 5:
                    self.stdout.write(f'      ... e mais {len(operations) - 5} operações')
        else:
            self.stdout.write('\n✅ Nenhuma operação de I/O lenta detectada')

        # Analisar erros
        if debugger.slow_operations:
            self.stdout.write('\n❌ Erros/Operações problemáticas:')
            for op_type, description, details in debugger.slow_operations:
                self.stdout.write(f'   🚨 {op_type}: {description}')
                if details and len(details) < 200:
                    self.stdout.write(f'      Detalhes: {details}')

        # Recomendações baseadas nos resultados
        self.generate_recommendations(debugger)

    def generate_recommendations(self, debugger):
        """Gera recomendações baseadas nos resultados"""
        self.stdout.write('\n💡 RECOMENDAÇÕES:')

        # Analisar onde foi gasto mais tempo
        if debugger.checkpoints:
            slowest_step = max(debugger.checkpoints, key=lambda x: x[1])
            step_name, step_time = slowest_step

            if step_time > 5:
                self.stdout.write(f'   🎯 Foco principal: "{step_name}" ({step_time:.3f}s)')

                if 'get_handler' in step_name:
                    self.stdout.write('      - Problema no carregamento de URLs/middleware')
                    self.stdout.write('      - Verificar URLs.py complexos ou middleware pesado')
                elif 'inner_run' in step_name:
                    self.stdout.write('      - Problema na inicialização do servidor')
                    self.stdout.write('      - Verificar configurações de desenvolvimento')
                elif 'check_migrations' in step_name:
                    self.stdout.write('      - Problema na verificação de migrações')
                    self.stdout.write('      - Banco de dados pode estar lento')

        # Recomendações baseadas em I/O
        if debugger.io_operations:
            file_ops = [op for op in debugger.io_operations if op[0] in ['open', 'stat']]
            dir_ops = [op for op in debugger.io_operations if op[0] in ['listdir', 'walk']]

            if file_ops:
                self.stdout.write('   📁 Otimizar acesso a arquivos:')
                self.stdout.write('      - Verificar StatReloader (auto-reload)')
                self.stdout.write('      - Considerar --noreload para desenvolvimento')

            if dir_ops:
                self.stdout.write('   📂 Otimizar scan de diretórios:')
                self.stdout.write('      - Muitos arquivos podem estar sendo monitorados')
                self.stdout.write('      - Verificar STATICFILES_DIRS')

        self.stdout.write('\n🔧 Comandos úteis para testar:')
        self.stdout.write('   python manage.py runserver --noreload')
        self.stdout.write('   python manage.py runserver --nostatic')
        self.stdout.write('   python manage.py collectstatic --noinput')
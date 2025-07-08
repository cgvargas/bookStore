# cgbookstore/apps/core/management/commands/system_profiler.py

import os
import time
import threading
import subprocess
import sys
from collections import defaultdict
from django.core.management.base import BaseCommand


class SystemProfiler:
    """Profiler completo do sistema para identificar gargalos"""

    def __init__(self, stdout):
        self.stdout = stdout
        self.start_time = time.time()
        self.import_times = {}
        self.system_stats = []
        self.thread_activity = []
        self.is_monitoring = True

    def monitor_imports(self):
        """Monitora tempo de importação de módulos"""
        import builtins
        original_import = builtins.__import__

        def timed_import(name, *args, **kwargs):
            start_time = time.time()
            result = original_import(name, *args, **kwargs)
            elapsed = time.time() - start_time

            # Registrar apenas importações que demoram > 0.01s
            if elapsed > 0.01:
                total_elapsed = time.time() - self.start_time
                self.import_times[name] = {
                    'duration': elapsed,
                    'timestamp': total_elapsed
                }

                if elapsed > 1.0:
                    self.stdout.write(f'   🚨 {total_elapsed:.1f}s: Import "{name}" demorou {elapsed:.3f}s')
                elif elapsed > 0.1:
                    self.stdout.write(f'   ⚠️ {total_elapsed:.1f}s: Import "{name}" demorou {elapsed:.3f}s')

            return result

        builtins.__import__ = timed_import
        return original_import

    def monitor_system_resources(self):
        """Monitora recursos do sistema em background"""

        def monitor_loop():
            try:
                # Importar psutil apenas se disponível
                try:
                    import psutil
                    has_psutil = True
                except ImportError:
                    has_psutil = False

                while self.is_monitoring:
                    timestamp = time.time() - self.start_time

                    if has_psutil:
                        try:
                            # Estatísticas básicas
                            cpu_percent = psutil.cpu_percent()
                            memory = psutil.virtual_memory()

                            # Estatísticas de I/O
                            disk_io = psutil.disk_io_counters()
                            net_io = psutil.net_io_counters()

                            # Processos Python
                            python_processes = []
                            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                                try:
                                    if 'python' in proc.info['name'].lower():
                                        python_processes.append(proc.info)
                                except:
                                    continue

                            self.system_stats.append({
                                'timestamp': timestamp,
                                'cpu_percent': cpu_percent,
                                'memory_percent': memory.percent,
                                'disk_read': disk_io.read_bytes if disk_io else 0,
                                'disk_write': disk_io.write_bytes if disk_io else 0,
                                'net_sent': net_io.bytes_sent if net_io else 0,
                                'net_recv': net_io.bytes_recv if net_io else 0,
                                'python_processes': len(python_processes)
                            })

                        except Exception as e:
                            # Em caso de erro, continuar sem psutil
                            pass
                    else:
                        # Monitoramento básico sem psutil
                        self.system_stats.append({
                            'timestamp': timestamp,
                            'basic_monitoring': True
                        })

                    time.sleep(0.5)  # Amostragem a cada 500ms

            except Exception as e:
                self.stdout.write(f'   ❌ Erro no monitoramento: {e}')

        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        return monitor_thread

    def monitor_thread_activity(self):
        """Monitora atividade de threads"""

        def thread_monitor():
            while self.is_monitoring:
                active_threads = threading.active_count()
                thread_names = [t.name for t in threading.enumerate()]

                timestamp = time.time() - self.start_time
                self.thread_activity.append({
                    'timestamp': timestamp,
                    'active_count': active_threads,
                    'thread_names': thread_names.copy()
                })

                time.sleep(1.0)  # Verificar threads a cada segundo

        thread_monitor_thread = threading.Thread(target=thread_monitor, daemon=True)
        thread_monitor_thread.start()
        return thread_monitor_thread


class Command(BaseCommand):
    help = 'Profiler completo do sistema para identificar gargalos no runserver'

    def add_arguments(self, parser):
        parser.add_argument(
            '--duration',
            type=int,
            default=30,
            help='Duração do profiling em segundos (padrão: 30)'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔬 PROFILER COMPLETO DO SISTEMA\n')
        )

        duration = options['duration']
        profiler = SystemProfiler(self.stdout)

        self.stdout.write(f'📊 Iniciando profiling por {duration} segundos...')
        self.stdout.write('🚀 Execute "python manage.py runserver" em outro terminal AGORA!\n')

        # Ativar monitoramento de imports
        original_import = profiler.monitor_imports()

        # Iniciar monitoramento de recursos e threads
        resource_monitor = profiler.monitor_system_resources()
        thread_monitor = profiler.monitor_thread_activity()

        try:
            # Aguardar pelo tempo especificado
            for i in range(duration):
                elapsed = i + 1
                remaining = duration - elapsed
                self.stdout.write(f'⏱️ {elapsed}s elapsed, {remaining}s remaining...')
                time.sleep(1)

            # Parar monitoramento
            profiler.is_monitoring = False

            # Aguardar threads terminarem
            time.sleep(1)

            # Analisar resultados
            self.analyze_results(profiler)

        finally:
            # Restaurar import original
            import builtins
            builtins.__import__ = original_import

    def analyze_results(self, profiler):
        """Analisa todos os dados coletados"""
        self.stdout.write('\n📋 ANÁLISE COMPLETA DOS RESULTADOS:\n')

        # 1. Análise de imports
        self.analyze_imports(profiler)

        # 2. Análise de recursos do sistema
        self.analyze_system_resources(profiler)

        # 3. Análise de threads
        self.analyze_thread_activity(profiler)

        # 4. Conclusões e recomendações
        self.generate_conclusions(profiler)

    def analyze_imports(self, profiler):
        """Analisa importações lentas"""
        self.stdout.write('1️⃣ ANÁLISE DE IMPORTAÇÕES:')

        if not profiler.import_times:
            self.stdout.write('   ✅ Nenhuma importação lenta detectada')
            return

        # Ordenar por duração
        slow_imports = sorted(
            profiler.import_times.items(),
            key=lambda x: x[1]['duration'],
            reverse=True
        )

        total_import_time = sum(data['duration'] for _, data in slow_imports)

        self.stdout.write(f'   📊 Total de tempo em imports: {total_import_time:.3f}s')
        self.stdout.write(f'   📦 Número de imports lentos: {len(slow_imports)}')

        # Mostrar os 10 mais lentos
        self.stdout.write('\n   🐌 Imports mais lentos:')
        for module_name, data in slow_imports[:10]:
            duration = data['duration']
            timestamp = data['timestamp']

            if duration > 2.0:
                icon = '🚨'
            elif duration > 0.5:
                icon = '⚠️'
            else:
                icon = '📦'

            self.stdout.write(f'      {icon} {module_name}: {duration:.3f}s (aos {timestamp:.1f}s)')

    def analyze_system_resources(self, profiler):
        """Analisa recursos do sistema"""
        self.stdout.write('\n2️⃣ ANÁLISE DE RECURSOS DO SISTEMA:')

        if not profiler.system_stats:
            self.stdout.write('   ❌ Nenhum dado de sistema coletado')
            return

        # Verificar se temos dados completos
        has_cpu_data = any('cpu_percent' in stat for stat in profiler.system_stats)

        if has_cpu_data:
            # Calcular estatísticas
            cpu_values = [stat['cpu_percent'] for stat in profiler.system_stats if 'cpu_percent' in stat]
            memory_values = [stat['memory_percent'] for stat in profiler.system_stats if 'memory_percent' in stat]

            if cpu_values:
                avg_cpu = sum(cpu_values) / len(cpu_values)
                max_cpu = max(cpu_values)
                avg_memory = sum(memory_values) / len(memory_values)
                max_memory = max(memory_values)

                self.stdout.write(f'   🔥 CPU - Média: {avg_cpu:.1f}%, Máximo: {max_cpu:.1f}%')
                self.stdout.write(f'   🧠 Memória - Média: {avg_memory:.1f}%, Máximo: {max_memory:.1f}%')

                # Detectar picos
                if max_cpu > 80:
                    self.stdout.write('   🚨 Picos altos de CPU detectados!')
                if max_memory > 80:
                    self.stdout.write('   🚨 Uso alto de memória detectado!')

                # Análise de I/O
                disk_stats = [stat for stat in profiler.system_stats if 'disk_read' in stat]
                if len(disk_stats) > 1:
                    initial_read = disk_stats[0]['disk_read']
                    final_read = disk_stats[-1]['disk_read']
                    initial_write = disk_stats[0]['disk_write']
                    final_write = disk_stats[-1]['disk_write']

                    total_read = (final_read - initial_read) / (1024 * 1024)  # MB
                    total_write = (final_write - initial_write) / (1024 * 1024)  # MB

                    self.stdout.write(f'   💾 I/O Disco - Leitura: {total_read:.1f}MB, Escrita: {total_write:.1f}MB')

                    if total_read > 100 or total_write > 100:
                        self.stdout.write('   ⚠️ I/O de disco intenso detectado!')
        else:
            self.stdout.write('   ⚠️ psutil não disponível - monitoramento limitado')
            self.stdout.write(f'   📊 Amostras coletadas: {len(profiler.system_stats)}')

    def analyze_thread_activity(self, profiler):
        """Analisa atividade de threads"""
        self.stdout.write('\n3️⃣ ANÁLISE DE THREADS:')

        if not profiler.thread_activity:
            self.stdout.write('   ❌ Nenhum dado de thread coletado')
            return

        # Analisar mudanças no número de threads
        thread_counts = [activity['active_count'] for activity in profiler.thread_activity]

        if thread_counts:
            min_threads = min(thread_counts)
            max_threads = max(thread_counts)
            avg_threads = sum(thread_counts) / len(thread_counts)

            self.stdout.write(f'   🧵 Threads - Mín: {min_threads}, Máx: {max_threads}, Média: {avg_threads:.1f}')

            # Detectar picos de threads
            if max_threads > min_threads + 5:
                self.stdout.write('   ⚠️ Variação significativa no número de threads!')

            # Analisar nomes de threads mais comuns
            all_thread_names = []
            for activity in profiler.thread_activity:
                all_thread_names.extend(activity['thread_names'])

            # Contar threads por nome
            thread_name_counts = defaultdict(int)
            for name in all_thread_names:
                thread_name_counts[name] += 1

            # Mostrar threads mais ativas
            most_active = sorted(thread_name_counts.items(), key=lambda x: x[1], reverse=True)[:5]

            self.stdout.write('   🏃 Threads mais ativas:')
            for thread_name, count in most_active:
                self.stdout.write(f'      - {thread_name}: {count} ocorrências')

    def generate_conclusions(self, profiler):
        """Gera conclusões e recomendações"""
        self.stdout.write('\n4️⃣ CONCLUSÕES E RECOMENDAÇÕES:\n')

        # Análise de imports
        if profiler.import_times:
            slow_imports = [name for name, data in profiler.import_times.items() if data['duration'] > 1.0]
            if slow_imports:
                self.stdout.write('🎯 IMPORTS LENTOS DETECTADOS:')
                for module_name in slow_imports:
                    duration = profiler.import_times[module_name]['duration']
                    self.stdout.write(f'   - {module_name}: {duration:.3f}s')
                self.stdout.write('   💡 Investigar esses módulos para otimização\n')

        # Análise de sistema
        has_system_issues = False
        if profiler.system_stats and any('cpu_percent' in stat for stat in profiler.system_stats):
            cpu_values = [stat['cpu_percent'] for stat in profiler.system_stats if 'cpu_percent' in stat]
            if cpu_values and max(cpu_values) > 80:
                self.stdout.write('🔥 ALTO USO DE CPU:')
                self.stdout.write('   💡 Considerar otimização de código ou hardware')
                has_system_issues = True

        # Recomendações gerais
        self.stdout.write('🚀 PRÓXIMOS PASSOS:')

        if profiler.import_times:
            total_import_time = sum(data['duration'] for _, data in profiler.import_times.items())
            if total_import_time > 5.0:
                self.stdout.write('   1. Otimizar imports lentos identificados')

        self.stdout.write('   2. Executar com --noreload para eliminar StatReloader')
        self.stdout.write('   3. Considerar usar servidor WSGI ao invés de runserver')
        self.stdout.write('   4. Verificar configurações de rede/DNS se não há imports lentos')

        if not has_system_issues and not profiler.import_times:
            self.stdout.write('\n❓ Se nenhum gargalo óbvio foi detectado:')
            self.stdout.write('   - O problema pode estar em operações de rede síncronas')
            self.stdout.write('   - Verificar timeouts de conexão de serviços externos')
            self.stdout.write('   - Considerar executar strace/Process Monitor para I/O detalhado')
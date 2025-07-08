# cgbookstore/apps/core/management/commands/cache_import_finder.py

import time
import traceback
import sys
from django.core.management.base import BaseCommand
from django.core.cache import caches


class CacheAccessTracker:
    """Intercepta e rastreia todos os acessos ao cache durante importação"""

    def __init__(self, stdout):
        self.stdout = stdout
        self.access_log = []
        self.original_getitem = None
        self.start_time = time.time()

    def track_cache_access(self, cache_alias):
        """Registra um acesso ao cache com stack trace"""
        current_time = time.time()
        elapsed = current_time - self.start_time

        # Capturar stack trace para identificar o arquivo que está acessando
        stack = traceback.extract_stack()

        # Filtrar stack trace para mostrar apenas arquivos relevantes do projeto
        relevant_frames = []
        for frame in stack:
            filename = frame.filename
            # Incluir apenas arquivos do projeto (não do Django/Python)
            if any(path in filename.lower() for path in ['cgbookstore', 'bookstore']):
                relevant_frames.append({
                    'file': filename,
                    'line': frame.lineno,
                    'function': frame.name,
                    'code': frame.line
                })

        access_info = {
            'cache_alias': cache_alias,
            'timestamp': elapsed,
            'stack_frames': relevant_frames
        }

        self.access_log.append(access_info)

        # Log em tempo real
        if relevant_frames:
            top_frame = relevant_frames[-1]  # Frame mais específico
            file_short = top_frame['file'].split('\\')[-1] if '\\' in top_frame['file'] else \
            top_frame['file'].split('/')[-1]
            self.stdout.write(
                f'   🔍 {elapsed:.3f}s: Cache "{cache_alias}" acessado por {file_short}:{top_frame["line"]}')

        return elapsed


class Command(BaseCommand):
    help = 'Intercepta e encontra todos os acessos ao cache durante importação'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🕵️ INTERCEPTADOR DE ACESSO AO CACHE\n')
        )

        tracker = CacheAccessTracker(self.stdout)

        # Interceptar o método __getitem__ de caches
        original_getitem = caches.__class__.__getitem__

        def intercepted_getitem(self_caches, alias):
            """Intercepta caches['alias'] e registra o acesso"""
            start_access = time.time()
            tracker.track_cache_access(alias)

            try:
                result = original_getitem(self_caches, alias)
                access_time = time.time() - start_access

                if access_time > 0.1:
                    tracker.stdout.write(f'      ⚠️ Conexão lenta: {access_time:.3f}s')

                return result
            except Exception as e:
                access_time = time.time() - start_access
                tracker.stdout.write(f'      ❌ Erro na conexão: {e} ({access_time:.3f}s)')
                raise

        # Aplicar monkey patch
        caches.__class__.__getitem__ = intercepted_getitem

        try:
            self.stdout.write('1️⃣ Ativando interceptação de cache...')
            self.stdout.write('2️⃣ Simulando importação de apps (como no runserver)...\n')

            # Simular o processo de importação do runserver
            self.simulate_runserver_imports(tracker)

            # Analisar resultados
            self.analyze_cache_accesses(tracker)

        finally:
            # Restaurar método original
            caches.__class__.__getitem__ = original_getitem

    def simulate_runserver_imports(self, tracker):
        """Simula as importações que o runserver faz"""

        # Importações principais que o runserver faz
        imports_to_test = [
            # Apps do projeto
            ('cgbookstore.apps.core.models', 'Modelos Core'),
            ('cgbookstore.apps.core.views', 'Views Core'),
            ('cgbookstore.apps.core.recommendations.engine', 'Recommendation Engine'),
            ('cgbookstore.apps.core.services.google_books_service', 'Google Books Service'),
            ('cgbookstore.apps.core.utils.google_books_cache', 'Google Books Cache'),
            ('cgbookstore.apps.chatbot_literario.models', 'Chatbot Models'),

            # URLs (importante para runserver)
            ('cgbookstore.config.urls', 'URLs principais'),
            ('cgbookstore.apps.core.urls', 'URLs Core'),
            ('cgbookstore.apps.core.recommendations.urls', 'URLs Recommendations'),
        ]

        for module_name, description in imports_to_test:
            try:
                self.stdout.write(f'📦 Importando {description}...')
                start_time = time.time()

                # Remover módulo do cache se já foi importado
                if module_name in sys.modules:
                    del sys.modules[module_name]

                # Importar módulo
                __import__(module_name)

                import_time = time.time() - start_time

                if import_time > 1.0:
                    self.stdout.write(f'   🚨 {description}: {import_time:.3f}s (MUITO LENTO)')
                elif import_time > 0.2:
                    self.stdout.write(f'   ⚠️ {description}: {import_time:.3f}s')
                else:
                    self.stdout.write(f'   ✅ {description}: {import_time:.3f}s')

            except ImportError as e:
                self.stdout.write(f'   ❌ {description}: Não encontrado - {e}')
            except Exception as e:
                self.stdout.write(f'   💥 {description}: ERRO - {e}')

    def analyze_cache_accesses(self, tracker):
        """Analisa todos os acessos ao cache registrados"""
        self.stdout.write(f'\n📊 ANÁLISE DOS ACESSOS AO CACHE:\n')

        if not tracker.access_log:
            self.stdout.write('✅ Nenhum acesso ao cache durante importação detectado!')
            return

        # Agrupar por arquivo
        by_file = {}
        by_cache = {}

        for access in tracker.access_log:
            cache_alias = access['cache_alias']

            # Agrupar por cache
            if cache_alias not in by_cache:
                by_cache[cache_alias] = []
            by_cache[cache_alias].append(access)

            # Agrupar por arquivo
            if access['stack_frames']:
                top_frame = access['stack_frames'][-1]
                file_key = f"{top_frame['file']}:{top_frame['line']}"

                if file_key not in by_file:
                    by_file[file_key] = []
                by_file[file_key].append(access)

        # Mostrar por cache
        self.stdout.write('🔍 ACESSOS POR CACHE:')
        for cache_name, accesses in by_cache.items():
            self.stdout.write(f'   📦 Cache "{cache_name}": {len(accesses)} acessos')

            # Mostrar timing dos acessos
            times = [acc['timestamp'] for acc in accesses]
            if times:
                first_access = min(times)
                last_access = max(times)
                self.stdout.write(f'      ⏱️ Primeiro acesso: {first_access:.3f}s')
                self.stdout.write(f'      ⏱️ Último acesso: {last_access:.3f}s')

        # Mostrar por arquivo (os culpados!)
        self.stdout.write(f'\n🎯 ARQUIVOS CULPADOS:')
        for file_info, accesses in by_file.items():
            file_path, line_num = file_info.rsplit(':', 1)
            file_name = file_path.split('\\')[-1] if '\\' in file_path else file_path.split('/')[-1]

            caches_accessed = set(acc['cache_alias'] for acc in accesses)

            self.stdout.write(f'   🚨 {file_name}:{line_num}')
            self.stdout.write(f'      Caches acessados: {", ".join(caches_accessed)}')
            self.stdout.write(f'      Número de acessos: {len(accesses)}')

            # Mostrar código se disponível
            if accesses[0]['stack_frames']:
                code_line = accesses[0]['stack_frames'][-1]['code']
                if code_line:
                    self.stdout.write(f'      Código: {code_line.strip()}')

        # Recomendações
        self.stdout.write(f'\n💡 CORREÇÕES NECESSÁRIAS:')

        for file_info, accesses in by_file.items():
            file_path, line_num = file_info.rsplit(':', 1)
            file_name = file_path.split('\\')[-1] if '\\' in file_path else file_path.split('/')[-1]

            self.stdout.write(f'\n   📝 {file_name}:')
            self.stdout.write(f'      - Mover acesso ao cache para dentro de métodos')
            self.stdout.write(f'      - Usar lazy loading (property ou método)')
            self.stdout.write(f'      - Evitar cache = caches[...] no nível de classe')

            # Sugerir padrão de correção
            caches_used = set(acc['cache_alias'] for acc in accesses)
            for cache_name in caches_used:
                self.stdout.write(f'      - Substituir: cache = caches["{cache_name}"]')
                self.stdout.write(f'      - Por: def get_cache(): return caches["{cache_name}"]')

        self.stdout.write(f'\n🎯 TOTAL: {len(by_file)} arquivos precisam ser corrigidos')
from django.core.management.base import BaseCommand
from django.core.cache import caches
from django.conf import settings
import redis


class Command(BaseCommand):
    help = 'Exibe informações detalhadas sobre a conexão Redis'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cache',
            type=str,
            default='default',
            help='Nome do cache a ser verificado (default: default)'
        )
        parser.add_argument(
            '--keys',
            action='store_true',
            help='Lista todas as chaves do Redis'
        )
        parser.add_argument(
            '--pattern',
            type=str,
            help='Padrão para filtrar chaves (ex: user:*)'
        )

    def handle(self, *args, **options):
        cache_name = options['cache']

        try:
            # Obter cache configurado
            cache = caches[cache_name]
            client = cache.client.get_client(write=True)

            self.stdout.write(
                self.style.SUCCESS(f'\n=== INFORMAÇÕES DO REDIS - CACHE: {cache_name} ===\n')
            )

            # Informações de conexão
            conn_info = client.connection_pool.connection_kwargs
            self.stdout.write('📡 CONEXÃO:')
            self.stdout.write(f'   Host: {conn_info.get("host", "N/A")}')
            self.stdout.write(f'   Porta: {conn_info.get("port", "N/A")}')
            self.stdout.write(f'   Database: {conn_info.get("db", "N/A")}')
            self.stdout.write(f'   Password: {"***" if conn_info.get("password") else "Não configurada"}')

            # Testar conexão
            try:
                ping_result = client.ping()
                self.stdout.write(f'   Status: {"✅ Conectado" if ping_result else "❌ Desconectado"}')
            except Exception as e:
                self.stdout.write(f'   Status: ❌ Erro na conexão: {e}')
                return

            # Informações do servidor
            self.stdout.write('\n🔧 SERVIDOR:')
            try:
                info = client.info()
                self.stdout.write(f'   Versão Redis: {info.get("redis_version", "N/A")}')
                self.stdout.write(f'   Modo: {info.get("redis_mode", "N/A")}')
                self.stdout.write(f'   Uptime: {info.get("uptime_in_seconds", 0)} segundos')
                self.stdout.write(f'   Memória usada: {info.get("used_memory_human", "N/A")}')
                self.stdout.write(f'   Conexões: {info.get("connected_clients", "N/A")}')
            except Exception as e:
                self.stdout.write(f'   Erro ao obter info do servidor: {e}')

            # Informações do database
            self.stdout.write('\n💾 DATABASE:')
            try:
                db_info = client.info('keyspace')
                db_num = conn_info.get('db', 0)
                db_key = f'db{db_num}'

                if db_key in db_info:
                    db_stats = db_info[db_key]
                    self.stdout.write(f'   Database {db_num}: {db_stats}')
                else:
                    self.stdout.write(f'   Database {db_num}: Vazio (0 chaves)')

                # Total de chaves
                total_keys = client.dbsize()
                self.stdout.write(f'   Total de chaves: {total_keys}')

            except Exception as e:
                self.stdout.write(f'   Erro ao obter info do database: {e}')

            # Listar chaves se solicitado
            if options['keys'] or options['pattern']:
                self.stdout.write('\n🔑 CHAVES:')
                try:
                    pattern = options['pattern'] or '*'
                    keys = client.keys(pattern)

                    if keys:
                        self.stdout.write(f'   Padrão: {pattern}')
                        self.stdout.write(f'   Encontradas: {len(keys)} chaves')
                        self.stdout.write('   Lista:')

                        for key in sorted(keys):
                            key_str = key.decode('utf-8') if isinstance(key, bytes) else str(key)
                            try:
                                key_type = client.type(key).decode('utf-8')
                                ttl = client.ttl(key)
                                ttl_info = f" (TTL: {ttl}s)" if ttl > 0 else " (sem expiração)" if ttl == -1 else " (expirada)"
                                self.stdout.write(f'     • {key_str} [{key_type}]{ttl_info}')
                            except Exception:
                                self.stdout.write(f'     • {key_str}')
                    else:
                        self.stdout.write(f'   Nenhuma chave encontrada com o padrão: {pattern}')

                except Exception as e:
                    self.stdout.write(f'   Erro ao listar chaves: {e}')

            # Configurações Django
            self.stdout.write('\n⚙️  CONFIGURAÇÃO DJANGO:')
            try:
                cache_config = settings.CACHES.get(cache_name, {})
                self.stdout.write(f'   Backend: {cache_config.get("BACKEND", "N/A")}')
                self.stdout.write(f'   Location: {cache_config.get("LOCATION", "N/A")}')

                options_config = cache_config.get('OPTIONS', {})
                if options_config:
                    self.stdout.write('   Opções:')
                    for key, value in options_config.items():
                        self.stdout.write(f'     {key}: {value}')

            except Exception as e:
                self.stdout.write(f'   Erro ao obter configurações: {e}')

            self.stdout.write(f'\n{"=" * 50}\n')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao conectar com o cache "{cache_name}": {e}')
            )
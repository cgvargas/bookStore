import time
from django.core.management.base import BaseCommand
from django.core.cache import caches
from django.db import connections
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Gerencia a migração do DatabaseCache para o Redis'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mode',
            type=str,
            default='clear',
            choices=['clear', 'create_tables', 'validate', 'info'],
            help='Modo de operação: clear=limpar caches, create_tables=criar tabelas de cache, '
                 'validate=verificar conexão com Redis, info=mostrar informações'
        )

    def handle(self, *args, **options):
        mode = options['mode']

        if mode == 'clear':
            self.clear_all_caches()
        elif mode == 'create_tables':
            self.create_cache_tables()
        elif mode == 'validate':
            self.validate_redis_connection()
        elif mode == 'info':
            self.show_cache_info()

    def clear_all_caches(self):
        """Limpa todos os caches configurados"""
        self.stdout.write(self.style.WARNING('Limpando todos os caches...'))

        # Obter todas as chaves de cache configuradas
        cache_keys = settings.CACHES.keys()

        for cache_name in cache_keys:
            try:
                cache = caches[cache_name]
                self.stdout.write(f'Limpando cache "{cache_name}"...')
                cache.clear()
                self.stdout.write(self.style.SUCCESS(f'Cache "{cache_name}" limpo com sucesso.'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Erro ao limpar cache "{cache_name}": {str(e)}'))

        self.stdout.write(self.style.SUCCESS('Todos os caches foram limpos.'))

    def create_cache_tables(self):
        """Cria tabelas de cache do Django no banco de dados"""
        from django.core.management import call_command

        self.stdout.write(self.style.WARNING('Criando tabelas de cache no banco de dados...'))
        try:
            call_command('createcachetable')
            self.stdout.write(self.style.SUCCESS('Tabelas de cache criadas com sucesso.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao criar tabelas de cache: {str(e)}'))

    def validate_redis_connection(self):
        """Valida a conexão com o Redis para todos os caches configurados"""
        import redis

        self.stdout.write(self.style.WARNING('Validando conexões com Redis...'))

        all_successful = True
        for cache_name, cache_config in settings.CACHES.items():
            if 'django_redis' in cache_config.get('BACKEND', ''):
                try:
                    # Obter cache e verificar conexão
                    cache = caches[cache_name]
                    client = cache.client.get_client()

                    # Testar conexão
                    test_key = f'test_connection_{int(time.time())}'
                    client.set(test_key, 'test_value')
                    value = client.get(test_key)
                    client.delete(test_key)

                    if value == b'test_value':
                        self.stdout.write(self.style.SUCCESS(
                            f'Cache "{cache_name}" conectado ao Redis com sucesso.'
                        ))
                    else:
                        all_successful = False
                        self.stdout.write(self.style.ERROR(
                            f'Cache "{cache_name}": Valor recuperado não corresponde ao esperado.'
                        ))
                except Exception as e:
                    all_successful = False
                    self.stdout.write(self.style.ERROR(
                        f'Erro ao conectar ao Redis para o cache "{cache_name}": {str(e)}'
                    ))
            else:
                self.stdout.write(
                    f'Cache "{cache_name}" não usa Redis (Backend: {cache_config.get("BACKEND")}).'
                )

        if all_successful:
            self.stdout.write(self.style.SUCCESS('Todas as conexões Redis estão funcionando corretamente!'))
        else:
            self.stdout.write(
                self.style.ERROR('Algumas conexões Redis apresentaram problemas. Verifique os logs acima.'))

    def show_cache_info(self):
        """Mostra informações sobre os caches configurados"""
        self.stdout.write(self.style.WARNING('Informações de cache:'))

        for cache_name, cache_config in settings.CACHES.items():
            self.stdout.write(self.style.NOTICE(f'\nCache: {cache_name}'))
            self.stdout.write(f'Backend: {cache_config.get("BACKEND")}')
            self.stdout.write(f'Location: {cache_config.get("LOCATION")}')
            self.stdout.write(f'Timeout: {cache_config.get("TIMEOUT")} segundos')

            # Mostrar informações específicas de Redis
            if 'django_redis' in cache_config.get('BACKEND', ''):
                try:
                    cache = caches[cache_name]
                    client = cache.client.get_client()

                    # Obter informações do Redis
                    info = client.info()

                    # Mostrar algumas estatísticas úteis
                    self.stdout.write('Estatísticas Redis:')
                    self.stdout.write(f' - Versão: {info.get("redis_version", "N/A")}')
                    self.stdout.write(f' - Memória usada: {info.get("used_memory_human", "N/A")}')
                    self.stdout.write(f' - Conexões ativas: {info.get("connected_clients", "N/A")}')
                    self.stdout.write(f' - Uptime: {info.get("uptime_in_days", "N/A")} dias')

                    # Tentar obter estatísticas específicas do banco usando o DB específico
                    db_number = cache_config.get('LOCATION', '').split('/')[-1]
                    db_stats = info.get(f'db{db_number}', {})
                    if db_stats:
                        self.stdout.write(f' - Chaves no banco {db_number}: {db_stats.get("keys", "N/A")}')

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Erro ao obter informações do Redis: {str(e)}'))
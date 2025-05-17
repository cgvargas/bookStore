# cgbookstore/apps/core/management/commands/clear_image_cache.py
import logging
from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.conf import settings
from django.db import connection

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Limpa o cache de imagens do Google Books para forçar o recarregamento'

    def handle(self, *args, **options):
        try:
            # Verificar qual tipo de cache está sendo usado
            cache_backend = settings.CACHES['default']['BACKEND']
            self.stdout.write(f"Cache backend utilizado: {cache_backend}")

            if 'DatabaseCache' in cache_backend:
                # Para cache de banco de dados, precisamos usar SQL para limpar
                self.clear_database_cache()
            else:
                # Para outros tipos de cache, tentar abordagem genérica
                self.clear_generic_cache()

            self.stdout.write(self.style.SUCCESS('Processo de limpeza de cache concluído'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao limpar cache: {str(e)}'))
            logger.error(f'Erro ao limpar cache de imagens: {str(e)}')

    def clear_database_cache(self):
        """Limpa entradas de cache armazenadas no banco de dados"""
        try:
            # Obter nome da tabela de cache (padrão é 'django_cache')
            cache_table = settings.CACHES['default'].get('LOCATION', 'django_cache')
            self.stdout.write(f"Limpando cache da tabela: {cache_table}")

            # Contar entradas relacionadas a imagens antes da limpeza
            with connection.cursor() as cursor:
                # Contar registros relacionados a imagens
                cursor.execute(
                    f"SELECT COUNT(*) FROM {cache_table} "
                    f"WHERE cache_key LIKE %s OR cache_key LIKE %s OR cache_key LIKE %s",
                    ['%img_proxy%', '%image_proxy%', '%books.google%']
                )
                count_before = cursor.fetchone()[0]
                self.stdout.write(f"Encontrados {count_before} registros de cache relacionados a imagens")

                # Deletar registros relacionados a imagens
                cursor.execute(
                    f"DELETE FROM {cache_table} "
                    f"WHERE cache_key LIKE %s OR cache_key LIKE %s OR cache_key LIKE %s",
                    ['%img_proxy%', '%image_proxy%', '%books.google%']
                )
                self.stdout.write(self.style.SUCCESS(f'Excluídos registros de cache de imagens'))

                # Deletar registros relacionados a recomendações
                cursor.execute(
                    f"DELETE FROM {cache_table} "
                    f"WHERE cache_key LIKE %s OR cache_key LIKE %s OR cache_key LIKE %s",
                    ['%google_books%', '%book_%', '%recommendations%']
                )
                self.stdout.write(self.style.SUCCESS(f'Excluídos registros de cache de recomendações'))

            self.stdout.write(self.style.SUCCESS('Cache de banco de dados limpo com sucesso'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao limpar cache de banco de dados: {str(e)}'))
            logger.error(f'Erro ao limpar cache de banco de dados: {str(e)}')

    def clear_generic_cache(self):
        """Tenta limpar o cache de forma genérica (para backends como Memcached)"""
        try:
            # Limpar cache específico
            cache.clear()
            self.stdout.write(self.style.SUCCESS('Cache limpo com sucesso usando método genérico'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao limpar cache genérico: {str(e)}'))
            logger.error(f'Erro ao limpar cache genérico: {str(e)}')
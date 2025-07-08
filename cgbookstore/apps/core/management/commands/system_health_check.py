# cgbookstore/apps/core/management/commands/system_health_check.py

from django.core.management.base import BaseCommand
from django.db import connection
from django.core.cache import caches
from django.conf import settings
import sys


class Command(BaseCommand):
    help = 'Verifica a saúde geral do sistema'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🏥 HEALTH CHECK DO SISTEMA CGBookstore\n')
        )

        # 1. Verificar banco de dados
        self.stdout.write('🗄️ Verificando banco de dados...')
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            if result:
                self.stdout.write('   ✅ Banco de dados: OK')
            else:
                self.stdout.write('   ❌ Banco de dados: ERRO')
        except Exception as e:
            self.stdout.write(f'   ❌ Banco de dados: ERRO - {e}')

        # 2. Verificar caches
        self.stdout.write('\n💾 Verificando caches...')
        cache_names = ['default', 'recommendations', 'google_books', 'image_proxy']

        for cache_name in cache_names:
            try:
                cache = caches[cache_name]
                cache.set('health_check', 'test', 10)
                value = cache.get('health_check')
                if value == 'test':
                    self.stdout.write(f'   ✅ Cache {cache_name}: OK')
                    cache.delete('health_check')
                else:
                    self.stdout.write(f'   ❌ Cache {cache_name}: ERRO')
            except Exception as e:
                self.stdout.write(f'   ❌ Cache {cache_name}: ERRO - {e}')

        # 3. Verificar configurações
        self.stdout.write('\n⚙️ Verificando configurações...')

        # DEBUG
        if settings.DEBUG:
            self.stdout.write('   ⚠️ DEBUG: Ativo (não recomendado para produção)')
        else:
            self.stdout.write('   ✅ DEBUG: Desativado')

        # SECRET_KEY
        if hasattr(settings, 'SECRET_KEY') and len(settings.SECRET_KEY) > 20:
            self.stdout.write('   ✅ SECRET_KEY: Configurada')
        else:
            self.stdout.write('   ❌ SECRET_KEY: Não configurada adequadamente')

        # 4. Verificar Python e Django
        self.stdout.write('\n🐍 Informações do sistema...')
        self.stdout.write(f'   Python: {sys.version.split()[0]}')

        try:
            import django
            self.stdout.write(f'   Django: {django.get_version()}')
        except:
            self.stdout.write('   ❌ Django: Erro ao obter versão')

        # 5. Verificar models principais
        self.stdout.write('\n📚 Verificando modelos...')
        try:
            from cgbookstore.apps.core.models.book import Book
            book_count = Book.objects.count()
            self.stdout.write(f'   ✅ Books: {book_count} registros')
        except Exception as e:
            self.stdout.write(f'   ❌ Books: ERRO - {e}')

        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user_count = User.objects.count()
            self.stdout.write(f'   ✅ Users: {user_count} registros')
        except Exception as e:
            self.stdout.write(f'   ❌ Users: ERRO - {e}')

        self.stdout.write('\n✅ Health Check concluído!')
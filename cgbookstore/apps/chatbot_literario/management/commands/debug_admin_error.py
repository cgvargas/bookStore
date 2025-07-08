# Criar arquivo: chatbot_literario/management/commands/debug_admin_error.py

from django.core.management.base import BaseCommand
from django.urls import reverse
import traceback


class Command(BaseCommand):
    help = 'Debug detalhado dos erros do admin'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Iniciando debug detalhado...")

        # 1. Testar imports das views
        self.stdout.write("\n1. Testando imports das views...")
        try:
            from cgbookstore.apps.chatbot_literario.admin_views import (
                system_statistics, system_config, run_add_specific_dates,
                run_debug_chatbot, clean_knowledge_base
            )
            self.stdout.write(self.style.SUCCESS("✅ Todas as views importadas com sucesso"))
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f"❌ Erro de import: {e}"))
            return

        # 2. Testar se as URLs estão sendo registradas
        self.stdout.write("\n2. Testando resolução de URLs...")
        test_urls = [
            'system_statistics',
            'system_config',
            'run_add_specific_dates',
            'run_debug_chatbot',
            'clean_knowledge_base'
        ]

        for url_name in test_urls:
            try:
                url = reverse(url_name)
                self.stdout.write(self.style.SUCCESS(f"✅ {url_name}: {url}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ {url_name}: {e}"))

        # 3. Testar execução direta das views
        self.stdout.write("\n3. Testando execução das views...")

        from django.test import RequestFactory
        from django.contrib.auth import get_user_model  # ← Mudança aqui

        User = get_user_model()  # ← Mudança aqui
        factory = RequestFactory()

        # Criar usuário staff se não existir
        user = User.objects.filter(is_staff=True).first()
        if not user:
            self.stdout.write(self.style.WARNING("⚠️ Criando usuário staff para teste..."))
            try:
                user = User.objects.create_user(
                    username='test_admin',
                    email='test@example.com',  # ← Adicionar email se necessário
                    is_staff=True,
                    is_superuser=True
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Erro ao criar usuário: {e}"))
                return

        # Testar view system_statistics
        try:
            request = factory.get('/test/')
            request.user = user

            response = system_statistics(request)
            self.stdout.write(self.style.SUCCESS(f"✅ system_statistics executada: status {response.status_code}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ system_statistics falhou: {e}"))
            self.stdout.write(traceback.format_exc())

        # 4. Verificar estrutura do get_admin_urls
        self.stdout.write("\n4. Verificando get_admin_urls...")
        try:
            from cgbookstore.apps.chatbot_literario.admin_views import get_admin_urls
            urls = get_admin_urls()

            self.stdout.write(f"Total de URLs registradas: {len(urls)}")

            for url_pattern in urls:
                if hasattr(url_pattern, 'name') and url_pattern.name:
                    if 'statistics' in url_pattern.name or 'config' in url_pattern.name:
                        self.stdout.write(f"  📍 {url_pattern.pattern} -> {url_pattern.name}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erro em get_admin_urls: {e}"))

        # 5. Verificar se as views têm os decorators corretos
        self.stdout.write("\n5. Verificando decorators...")

        import inspect

        views_to_check = [system_statistics, system_config, run_add_specific_dates]

        for view in views_to_check:
            if hasattr(view, '__wrapped__'):
                self.stdout.write(f"✅ {view.__name__} tem decorator")
            else:
                self.stdout.write(f"⚠️ {view.__name__} pode não ter decorator staff_member_required")

        self.stdout.write(self.style.SUCCESS("\n🎯 Debug concluído!"))
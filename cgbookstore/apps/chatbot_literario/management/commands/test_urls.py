# Criar arquivo: chatbot_literario/management/commands/test_urls.py

from django.core.management.base import BaseCommand
from django.urls import reverse, NoReverseMatch


class Command(BaseCommand):
    help = 'Testa se as URLs do admin estão funcionando'

    def handle(self, *args, **options):
        urls_to_test = [
            'chatbot_literario_training',
            'run_add_specific_dates',
            'run_debug_chatbot',
            'clean_knowledge_base',
            'system_statistics',
            'system_config',
        ]

        self.stdout.write("Testando URLs do admin...")

        for url_name in urls_to_test:
            try:
                url = reverse(url_name)
                self.stdout.write(self.style.SUCCESS(f"✅ {url_name}: {url}"))
            except NoReverseMatch as e:
                self.stdout.write(self.style.ERROR(f"❌ {url_name}: {str(e)}"))

        # Testar se as views existem
        from cgbookstore.apps.chatbot_literario import admin_views

        views_to_test = [
            'run_add_specific_dates',
            'run_debug_chatbot',
            'clean_knowledge_base',
            'system_statistics',
            'system_config',
        ]

        self.stdout.write("\nTestando se as views existem...")

        for view_name in views_to_test:
            if hasattr(admin_views, view_name):
                self.stdout.write(self.style.SUCCESS(f"✅ View {view_name} existe"))
            else:
                self.stdout.write(self.style.ERROR(f"❌ View {view_name} NÃO existe"))

        # Listar todas as URLs disponíveis
        from cgbookstore.apps.chatbot_literario.admin_views import get_admin_urls

        self.stdout.write("\nURLs registradas em get_admin_urls():")
        try:
            urls = get_admin_urls()
            for url_pattern in urls:
                self.stdout.write(f"  - {url_pattern.pattern} -> {url_pattern.name}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao listar URLs: {str(e)}"))
# Criar arquivo: chatbot_literario/management/commands/test_view_direct.py

from django.core.management.base import BaseCommand
from django.test import RequestFactory
from django.contrib.auth import get_user_model  # ← Mudança aqui
from cgbookstore.apps.chatbot_literario.admin_views import system_statistics


class Command(BaseCommand):
    help = 'Testa diretamente a view system_statistics'

    def handle(self, *args, **options):
        # Criar request factory
        factory = RequestFactory()

        # Criar um request GET
        request = factory.get('/admin/chatbot/treinamento/statistics/')

        # Usar get_user_model() para o modelo customizado
        User = get_user_model()
        user = User.objects.filter(is_staff=True).first()

        if not user:
            self.stdout.write(self.style.ERROR("Nenhum usuário staff encontrado"))
            # Tentar criar um usuário staff
            try:
                user = User.objects.create_user(
                    username='test_admin',
                    email='test@example.com',
                    is_staff=True,
                    is_superuser=True
                )
                self.stdout.write(self.style.SUCCESS("Usuário staff criado para teste"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erro ao criar usuário: {e}"))
                return

        request.user = user

        try:
            # Chamar a view diretamente
            response = system_statistics(request)
            self.stdout.write(self.style.SUCCESS(f"✅ View executada com sucesso! Status: {response.status_code}"))

            if hasattr(response, 'content'):
                content_length = len(response.content)
                self.stdout.write(f"Tamanho do conteúdo: {content_length} bytes")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erro ao executar view: {str(e)}"))
            import traceback
            self.stdout.write(traceback.format_exc())
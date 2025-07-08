# cgbookstore/apps/chatbot_literario/management/commands/ollama.py

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import requests
import logging

# ✅ CORREÇÃO: Importar as instâncias de serviço e funções corretas e atuais
from cgbookstore.apps.chatbot_literario.services import ai_service, is_ai_available, functional_chatbot

# from cgbookstore.apps.chatbot_literario.services.embeddings import embeddings_service # Descomente se precisar

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Gerencia e diagnostica o serviço Ollama para o chatbot literário.'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            type=str,
            nargs='?',
            default='status',
            choices=['status', 'test'],  # Simplificado para os comandos que funcionam
            help='Ação a ser executada (status, test).',
        )
        parser.add_argument(
            '--prompt',
            type=str,
            default='Olá! Em uma frase, quem é você?',
            help='Prompt para o subcomando de teste.'
        )

    def handle(self, *args, **options):
        action = options['action']

        self.stdout.write(f"Ambiente de: {settings.DEBUG and 'development' or 'production'}")

        if action == 'status':
            self.show_status()
        elif action == 'test':
            self.test_prompt(options['prompt'])
        else:
            raise CommandError(f"Ação desconhecida: '{action}'. Use 'status' ou 'test'.")

    def show_status(self):
        """Exibe o status completo dos serviços de IA."""
        self.stdout.write(self.style.SUCCESS("\n📊 Verificando status dos serviços de IA..."))

        # 1. Configurações do Django
        self.stdout.write("\n" + self.style.WARNING("🔧 Configuração Django:"))
        try:
            # Tenta ler do dicionário primeiro (melhor prática)
            ollama_config = settings.OLLAMA_CONFIG
            enabled = ollama_config.get('enabled')
            model = ollama_config.get('model')
            url = ollama_config.get('base_url')
        except AttributeError:
            # Fallback para variáveis soltas (compatibilidade)
            enabled = getattr(settings, 'USE_OLLAMA', False)
            model = getattr(settings, 'OLLAMA_MODEL', None)
            url = getattr(settings, 'OLLAMA_URL', None)

        self.stdout.write(f"  Habilitado: {'✅' if enabled else '❌'}")
        self.stdout.write(f"  Modelo configurado: {model}")
        self.stdout.write(f"  URL: {url}")

        # 2. Status do AI Service (Ollama)
        self.stdout.write("\n" + self.style.WARNING("🤖 AI Service (Ollama):"))
        if is_ai_available():
            self.stdout.write(f"  Status: {'✅ Disponível'}")
            self.stdout.write(f"  URL: {ai_service.ollama_url}")
        else:
            self.stdout.write(self.style.ERROR("  Status: ❌ Indisponível"))
            self.stdout.write(f"  -> Verifique se o Ollama está rodando em {getattr(settings, 'OLLAMA_URL', url)}")

        # 3. Status do Chatbot Funcional
        self.stdout.write("\n" + self.style.WARNING("💬 Chatbot Funcional (Sessões em Memória):"))
        try:
            stats = functional_chatbot.get_statistics()
            self.stdout.write(f"  Sessões ativas: {stats.get('active_sessions', 'N/A')}")
            self.stdout.write(f"  Total de mensagens no histórico: {stats.get('total_messages', 'N/A')}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Não foi possível obter estatísticas do chatbot: {e}"))

        self.stdout.write(self.style.SUCCESS("\nVerificação de status concluída."))

    def test_prompt(self, prompt_text: str):
        """Envia um prompt de teste para o Ollama através da nossa camada de serviço."""
        self.stdout.write(self.style.SUCCESS(f"\n🧪 Enviando prompt de teste: '{prompt_text}'"))

        # ✅ CORREÇÃO: Usa a interface correta, que espera uma lista de mensagens
        messages_for_ai = [{"role": "user", "content": prompt_text}]

        response = ai_service.generate_response(messages_for_ai)

        if response.get('success'):
            self.stdout.write(self.style.SUCCESS("✅ Resposta recebida com sucesso!"))
            self.stdout.write(f"   Modelo ({response.get('model_used')}): '{response.get('response')}'")
        else:
            self.stdout.write(self.style.ERROR("❌ Falha ao obter resposta do Ollama."))
            self.stdout.write(f"   Erro: {response.get('error', 'Desconhecido')}")
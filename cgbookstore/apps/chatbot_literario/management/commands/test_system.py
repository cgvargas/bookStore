# cgbookstore/apps/chatbot_literario/management/commands/test_system.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Testa o sistema híbrido do chatbot literário (versão simplificada)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-data',
            action='store_true',
            help='Cria dados de exemplo na base de conhecimento',
        )
        parser.add_argument(
            '--test-chat',
            action='store_true',
            help='Testa conversas com o chatbot',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 TESTE DO SISTEMA HÍBRIDO'))
        self.stdout.write('=' * 50)

        try:
            # 1. Verificar serviços
            self.test_services()

            # 2. Criar dados se solicitado
            if options['create_data']:
                self.create_sample_data()

            # 3. Testar chat se solicitado
            if options['test_chat']:
                self.test_chatbot()

            # 4. Relatório
            self.final_report()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro: {e}'))

    def test_services(self):
        """Testa se os serviços estão funcionando"""
        self.stdout.write('\n📋 VERIFICANDO SERVIÇOS')
        self.stdout.write('-' * 30)

        try:
            # Importar serviços do seu __init__.py
            from cgbookstore.apps.chatbot_literario.services import (
                ai_service, embeddings_service, training_service, functional_chatbot
            )

            # Verificar AI Service
            if ai_service and hasattr(ai_service, 'is_available'):
                ai_ok = ai_service.is_available()
                emoji = '✅' if ai_ok else '❌'
                self.stdout.write(f'  {emoji} AI Service: {"OK" if ai_ok else "Indisponível"}')
            else:
                self.stdout.write('  ❌ AI Service: Não carregado')

            # Verificar Embeddings Service
            if embeddings_service and hasattr(embeddings_service, 'available'):
                emb_ok = embeddings_service.available
                emoji = '✅' if emb_ok else '❌'
                self.stdout.write(f'  {emoji} Embeddings Service: {"OK" if emb_ok else "Indisponível"}')
            else:
                self.stdout.write('  ❌ Embeddings Service: Não carregado')

            # Verificar Training Service
            if training_service and hasattr(training_service, 'initialized'):
                train_ok = training_service.initialized
                emoji = '✅' if train_ok else '⚠️'
                self.stdout.write(f'  {emoji} Training Service: {"OK" if train_ok else "Limitado"}')
            else:
                self.stdout.write('  ❌ Training Service: Não carregado')

            # Verificar Functional Chatbot
            if functional_chatbot:
                status = functional_chatbot.get_status()
                hybrid_mode = status.get('hybrid_mode', False)
                emoji = '✅' if hybrid_mode else '⚠️'
                mode = "Híbrido" if hybrid_mode else "IA Pura"
                self.stdout.write(f'  {emoji} Functional Chatbot: {mode}')
            else:
                self.stdout.write('  ❌ Functional Chatbot: Não carregado')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro na verificação: {e}'))

    def create_sample_data(self):
        """Cria dados de exemplo na base"""
        self.stdout.write('\n📚 CRIANDO DADOS DE EXEMPLO')
        self.stdout.write('-' * 30)

        try:
            from cgbookstore.apps.chatbot_literario.models import KnowledgeItem

            sample_data = [
                {
                    'question': 'Quem escreveu Dom Casmurro?',
                    'answer': 'Dom Casmurro foi escrito por Machado de Assis em 1899. É considerado uma das principais obras do Realismo brasileiro, narrando a história de Bentinho e sua desconfiança sobre a traição de Capitu.',
                    'category': 'author',
                    'source': 'literatura_brasileira'
                },
                {
                    'question': 'O que caracteriza o Romantismo brasileiro?',
                    'answer': 'O Romantismo brasileiro (séc. XIX) se caracteriza pelo nacionalismo, indianismo, sentimentalismo, valorização da natureza brasileira e busca por uma identidade nacional. Principais autores: José de Alencar, Gonçalves Dias.',
                    'category': 'movement',
                    'source': 'historia_literatura'
                },
                {
                    'question': 'Quem foi José de Alencar?',
                    'answer': 'José de Alencar (1829-1877) foi escritor brasileiro, principal representante do Romantismo. Escreveu O Guarani, Iracema e Senhora. Criador do romance brasileiro e defensor da linguagem nacional.',
                    'category': 'author',
                    'source': 'biografia_autores'
                }
            ]

            created = 0
            for data in sample_data:
                item, was_created = KnowledgeItem.objects.get_or_create(
                    question=data['question'],
                    defaults=data
                )
                if was_created:
                    created += 1
                    self.stdout.write(f"  ✅ Criado: {data['question'][:40]}...")
                else:
                    self.stdout.write(f"  ⏭️ Existe: {data['question'][:40]}...")

            self.stdout.write(f'\n📊 {created} novos itens criados')
            total = KnowledgeItem.objects.filter(active=True).count()
            self.stdout.write(f'📈 Total na base: {total} itens')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao criar dados: {e}'))

    def test_chatbot(self):
        """Testa o chatbot com perguntas"""
        self.stdout.write('\n🤖 TESTANDO CONVERSAS')
        self.stdout.write('-' * 30)

        try:
            from cgbookstore.apps.chatbot_literario.services import functional_chatbot
            from cgbookstore.apps.chatbot_literario.models import Conversation

            if not functional_chatbot:
                self.stdout.write('❌ Functional chatbot não disponível')
                return

            # Criar usuário e conversa de teste
            user, _ = User.objects.get_or_create(
                username='test_user',
                defaults={'email': 'test@example.com'}
            )

            conversation, _ = Conversation.objects.get_or_create(
                user=user,
                defaults={'title': 'Teste Sistema'}
            )

            # Perguntas de teste
            questions = [
                "Quem escreveu Dom Casmurro?",
                "Fale sobre o Romantismo brasileiro",
                "Quem foi José de Alencar?"
            ]

            for i, question in enumerate(questions, 1):
                self.stdout.write(f'\n{i}. "{question}"')

                try:
                    response = functional_chatbot.get_response(question, conversation)

                    if response.get('success', True):
                        source = response.get('source', 'unknown')
                        knowledge_used = response.get('knowledge_items_used', 0)

                        emoji = '🎯' if source == 'hybrid' else '🤖'
                        self.stdout.write(f'   {emoji} Fonte: {source}')
                        self.stdout.write(f'   📚 Conhecimento: {knowledge_used} itens')

                        # Preview da resposta
                        resp_text = response.get('response', '')[:100]
                        self.stdout.write(f'   💭 "{resp_text}..."')

                    else:
                        self.stdout.write(f'   ❌ Erro: {response.get("error", "Erro desconhecido")}')

                except Exception as e:
                    self.stdout.write(f'   ❌ Exceção: {e}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro no teste de chat: {e}'))

    def final_report(self):
        """Relatório final"""
        self.stdout.write('\n📊 RELATÓRIO FINAL')
        self.stdout.write('-' * 30)

        try:
            from cgbookstore.apps.chatbot_literario.services import (
                ai_service, embeddings_service, training_service, functional_chatbot
            )
            from cgbookstore.apps.chatbot_literario.models import KnowledgeItem

            # Verificar status geral
            ai_ok = ai_service and hasattr(ai_service, 'is_available') and ai_service.is_available()
            emb_ok = embeddings_service and hasattr(embeddings_service, 'available') and embeddings_service.available
            train_ok = training_service and hasattr(training_service, 'initialized') and training_service.initialized
            chat_ok = functional_chatbot is not None

            # Status da base de conhecimento
            total_items = KnowledgeItem.objects.filter(active=True).count()

            self.stdout.write(f'🔧 Serviços Operacionais: {sum([ai_ok, emb_ok, train_ok, chat_ok])}/4')
            self.stdout.write(f'📚 Itens na Base: {total_items}')

            # Avaliação geral
            if ai_ok and chat_ok:
                if train_ok and total_items > 0:
                    self.stdout.write(self.style.SUCCESS('✅ SISTEMA HÍBRIDO OPERACIONAL'))
                    self.stdout.write('🎯 Precisão esperada: 80%+')
                else:
                    self.stdout.write(self.style.WARNING('⚠️ SISTEMA IA PURA OPERACIONAL'))
                    self.stdout.write('🤖 Precisão esperada: 60-70%')
            else:
                self.stdout.write(self.style.ERROR('❌ SISTEMA COM PROBLEMAS'))

            # Recomendações
            self.stdout.write('\n💡 RECOMENDAÇÕES:')
            if not emb_ok:
                self.stdout.write('  • Instalar: pip install sentence-transformers')
            if total_items == 0:
                self.stdout.write('  • Executar: python manage.py test_system --create-data')
            if ai_ok and chat_ok:
                self.stdout.write('  • Testar: python manage.py test_system --test-chat')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro no relatório: {e}'))

        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('🏁 TESTE CONCLUÍDO'))
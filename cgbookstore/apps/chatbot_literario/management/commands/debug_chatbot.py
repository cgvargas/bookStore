# cgbookstore/apps/chatbot_literario/management/commands/debug_chatbot.py

"""
Comando de debug para Chatbot Literário (VERSÃO ATUALIZADA)

Uso:
    python manage.py debug_chatbot test "pergunta teste"    # Testar pergunta
    python manage.py debug_chatbot context <user_id>        # Ver contexto do usuário
    python manage.py debug_chatbot knowledge                # Analisar base de conhecimento
    python manage.py debug_chatbot benchmark                # Benchmark de performance
    python manage.py debug_chatbot conversation <conv_id>   # Ver uma conversa
    python manage.py debug_chatbot integration              # Rodar testes de integração
"""

import time
import json
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import connection
from django.db.utils import OperationalError

# Importação corrigida para usar o novo serviço e os modelos
from ...models import Conversation, Message, KnowledgeItem
from ...services import chatbot_service

User = get_user_model()


class Command(BaseCommand):
    help = 'Debug e teste do sistema de chatbot literário (versão atualizada)'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            # --- CORREÇÃO AQUI ---
            # Adicionada a opção 'integration'
            choices=['test', 'context', 'knowledge', 'benchmark', 'conversation', 'integration'],
            help='Ação de debug a ser executada'
        )
        parser.add_argument(
            'query',
            nargs='?',
            help='Pergunta para teste ou ID do usuário/conversa'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='ID do usuário para contexto (usado em "test")'
        )
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Saída detalhada'
        )
        parser.add_argument(
            '--iterations',
            type=int,
            default=20,
            help='Número de iterações para benchmark'
        )

    def handle(self, *args, **options):
        action = options['action']

        try:
            # --- CORREÇÃO AQUI ---
            # Adicionado o handler para a nova ação
            if action == 'test':
                self.test_question(options)
            elif action == 'context':
                self.debug_context(options)
            elif action == 'knowledge':
                self.analyze_knowledge_base(options)
            elif action == 'benchmark':
                self.run_benchmark(options)
            elif action == 'conversation':
                self.debug_conversation(options)
            elif action == 'integration':
                self.run_integration_tests(options)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro: {str(e)}'))
            if options['detailed']:
                import traceback
                self.stdout.write(traceback.format_exc())

    def test_question(self, options):
        """Testa uma pergunta específica com debug detalhado."""
        if not options['query']:
            raise CommandError('Forneça uma pergunta para teste')

        question = options['query']
        user = None
        if options['user_id']:
            try:
                user = User.objects.get(id=options['user_id'])
                self.stdout.write(f"(Testando como usuário: {user.username})")
            except User.DoesNotExist:
                raise CommandError(f"Usuário com ID {options['user_id']} não encontrado.")

        self.stdout.write(self.style.SUCCESS('🧪 Teste de Pergunta'))
        self.stdout.write('=' * 50)
        self.stdout.write(f"📝 Pergunta: {question}")
        self.stdout.write('')

        debug_session_id = f"debug_session_{int(time.time())}"
        self.stdout.write(f"(ID de Sessão de Teste: {debug_session_id})")

        start_time = time.time()
        try:
            response_data = chatbot_service.get_response(
                message=question,
                user=user,
                session_id=debug_session_id
            )
            end_time = time.time()

            self.stdout.write(f"⚡ Tempo de resposta: {end_time - start_time:.3f}s")
            self.stdout.write(f"📊 Intenção Detectada: {response_data.get('intent', 'N/A')}")
            self.stdout.write(f"💬 Resposta: {response_data.get('response', 'N/A')}")
            self.stdout.write('')

            if options['detailed']:
                self.stdout.write('🔍 Resposta Completa (JSON):')
                self.stdout.write(json.dumps(response_data, indent=2, ensure_ascii=False))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erro no teste: {e}"))
            if options['detailed']:
                import traceback
                self.stdout.write(traceback.format_exc())

    def debug_context(self, options):
        """Debug do contexto de um usuário específico."""
        user_id = options.get('user_id') or options.get('query')
        if not user_id:
            raise CommandError('Forneça um ID de usuário')

        try:
            user = User.objects.get(id=int(user_id))
        except (ValueError, User.DoesNotExist):
            raise CommandError(f'Usuário {user_id} não encontrado')

        self.stdout.write(self.style.SUCCESS(f'👤 Debug de Contexto - Usuário: {user.username}'))
        self.stdout.write('=' * 60)

        try:
            conversation, created = Conversation.objects.get_or_create(user=user)
            context = conversation.get_context() if hasattr(conversation, 'get_context') else {}

            self.stdout.write(f"🆔 ID da Conversa: {conversation.id}")
            self.stdout.write(f"📅 Iniciada em: {conversation.started_at}")
            self.stdout.write(f"🔄 Atualizada em: {conversation.updated_at}")
            self.stdout.write('')

            self.stdout.write('🧠 Dados de Contexto (JSON):')
            self.stdout.write(json.dumps(context, indent=2, ensure_ascii=False))

        except Conversation.DoesNotExist:
            self.stdout.write('❌ Usuário não possui conversa ativa')

    def analyze_knowledge_base(self, options):
        """Analisa a base de conhecimento."""
        self.stdout.write(self.style.SUCCESS('📚 Análise da Base de Conhecimento'))
        self.stdout.write('=' * 60)
        total_items = KnowledgeItem.objects.count()
        active_items = KnowledgeItem.objects.filter(active=True).count()
        items_with_embedding = KnowledgeItem.objects.filter(active=True, embedding__isnull=False).exclude(embedding=[]).count()

        self.stdout.write(f"📊 Total de itens: {total_items}")
        self.stdout.write(f"✅ Itens ativos: {active_items}")
        self.stdout.write(f"🧠 Itens com embedding: {items_with_embedding} ({items_with_embedding/active_items:.1%} dos ativos)")

    def run_benchmark(self, options):
        """Executa benchmark de performance."""
        iterations = options['iterations']
        self.stdout.write(self.style.SUCCESS(f'⚡ Benchmark de Performance ({iterations} iterações)'))
        self.stdout.write('=' * 60)

        test_questions = ["Olá!", "Quem escreveu Dom Casmurro?", "Recomende um livro", "Obrigado!"]
        results = {'total_time': 0, 'intents': {}, 'errors': 0, 'times': []}

        for i in range(iterations):
            question = test_questions[i % len(test_questions)]
            start_time = time.time()
            try:
                response_data = chatbot_service.get_response(message=question, session_id=f"bench_{i}")
                end_time = time.time()

                response_time = end_time - start_time
                results['total_time'] += response_time
                results['times'].append(response_time)
                intent = response_data.get('intent', 'error')
                results['intents'][intent] = results['intents'].get(intent, 0) + 1

            except Exception:
                results['errors'] += 1

        avg_time = results['total_time'] / iterations if iterations > 0 else 0
        self.stdout.write('📊 Resultados do Benchmark:')
        self.stdout.write(f"  Tempo total: {results['total_time']:.2f}s")
        self.stdout.write(f"  Tempo médio por resposta: {avg_time:.3f}s")
        self.stdout.write(f"  Erros: {results['errors']}")
        self.stdout.write('🔄 Distribuição por Intenção:')
        for intent, count in results['intents'].items():
            self.stdout.write(f"  - {intent}: {count} vezes")

    def debug_conversation(self, options):
        """Debug de uma conversa específica."""
        conv_id = options.get('query')
        if not conv_id:
            raise CommandError("Forneça o ID da conversa.")

        try:
            conversation = Conversation.objects.get(id=int(conv_id))
        except (ValueError, Conversation.DoesNotExist):
            raise CommandError(f'Conversa {conv_id} não encontrada')

        self.stdout.write(self.style.SUCCESS(f'💬 Debug da Conversa #{conv_id}'))
        self.stdout.write(f"👤 Usuário: {conversation.user.username}")

        messages = Message.objects.filter(conversation=conversation).order_by('timestamp')
        for msg in messages:
            icon = '👤' if msg.sender == 'user' else '🤖'
            self.stdout.write(f"{icon} [{msg.timestamp.strftime('%H:%M:%S')}] - {msg.content}")

    # --- NOVA FUNÇÃO AQUI ---
    def run_integration_tests(self, options):
        """Executa testes de integração para os serviços do chatbot."""
        self.stdout.write(self.style.SUCCESS('🔗 Teste de Integração'))
        self.stdout.write('=' * 60)
        has_errors = False

        # 1. Teste de Conexão com o Banco de Dados
        self.stdout.write("1. Verificando conexão com o Banco de Dados...")
        try:
            connection.ensure_connection()
            self.stdout.write(self.style.SUCCESS("   ✅ Conexão OK."))
            # Testa uma query simples
            KnowledgeItem.objects.exists()
            self.stdout.write(self.style.SUCCESS("   ✅ Query de teste OK."))
        except OperationalError as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Falha na conexão com o DB: {e}"))
            has_errors = True

        # 2. Teste do Serviço de Embeddings
        self.stdout.write("\n2. Verificando Serviço de Embeddings...")
        if not chatbot_service.embeddings_service:
            self.stdout.write(self.style.ERROR("   ❌ Serviço de Embeddings não está disponível."))
            has_errors = True
        else:
            self.stdout.write(self.style.SUCCESS("   ✅ Serviço de Embeddings carregado."))
            try:
                # Tenta criar um embedding de teste
                embedding = chatbot_service.embeddings_service.create_embedding("teste de integração")
                if embedding is not None and len(embedding) > 0:
                    self.stdout.write(self.style.SUCCESS(f"   ✅ Criação de embedding de teste OK (dimensão: {len(embedding)})."))
                else:
                    self.stdout.write(self.style.ERROR("   ❌ Falha ao criar embedding (retornou None ou vazio)."))
                    has_errors = True
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ❌ Erro ao criar embedding de teste: {e}"))
                has_errors = True

        # Resumo final
        self.stdout.write('=' * 60)
        if has_errors:
            self.stdout.write(self.style.ERROR('🔴 Teste de integração concluído com erros.'))
        else:
            self.stdout.write(self.style.SUCCESS('🟢 Teste de integração concluído com sucesso.'))
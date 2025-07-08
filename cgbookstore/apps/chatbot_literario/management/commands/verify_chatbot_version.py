import logging
from django.core.management.base import BaseCommand
from cgbookstore.apps.core.models import User
from cgbookstore.apps.chatbot_literario.services.chatbot_service import chatbot
from cgbookstore.apps.chatbot_literario.services.training_service import training_service
import inspect
import sys


class Command(BaseCommand):
    help = 'Verifica se o chatbot está usando a versão corrigida e testa contexto'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            default=1,
            help='ID do usuário para teste (padrão: 1)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Saída detalhada'
        )

    def handle(self, *args, **options):
        user_id = options['user_id']
        verbose = options['verbose']

        # Configurar logging para capturar debug
        if verbose:
            logging.basicConfig(level=logging.DEBUG)

        self.stdout.write("=" * 60)
        self.stdout.write("🔍 VERIFICAÇÃO DA VERSÃO DO CHATBOT")
        self.stdout.write("=" * 60)

        # 1. Verificar se o chatbot está inicializado
        self.stdout.write("\n📋 1. Verificando inicialização...")
        if not chatbot.initialized:
            chatbot.initialize()
        self.stdout.write(f"   ✅ Chatbot inicializado: {chatbot.initialized}")

        # 2. Verificar métodos no código atual
        self.stdout.write("\n📋 2. Verificando métodos corrigidos...")

        # Verificar se os métodos corrigidos existem
        context_class = None
        if hasattr(chatbot, 'get_user_context'):
            user_context = chatbot.get_user_context(None) if chatbot.get_user_context else None
            if user_context:
                context_class = user_context.__class__

        chatbot_class = chatbot.__class__

        methods_to_check = [
            ('should_clear_context', context_class),
            ('_answer_contextual_question', chatbot_class),
            ('_extract_entities_preview', context_class),
            ('_is_contextual_question', chatbot_class)
        ]

        for method_name, target_class in methods_to_check:
            if target_class and hasattr(target_class, method_name):
                method = getattr(target_class, method_name)
                try:
                    source_lines = inspect.getsourcelines(method)[0]
                    self.stdout.write(f"   ✅ {method_name}: {len(source_lines)} linhas")

                    # Verificar se contém correções específicas
                    source_code = ''.join(source_lines)
                    if 'CORREÇÃO' in source_code or 'VERSÃO CORRIGIDA' in source_code:
                        self.stdout.write(f"      🎯 Contém marcações de correção")
                except Exception as e:
                    self.stdout.write(f"   ⚠️  {method_name}: Presente mas erro ao ler código: {e}")
            else:
                self.stdout.write(f"   ❌ {method_name}: NÃO ENCONTRADO")

        # 3. Verificar base de conhecimento
        self.stdout.write("\n📋 3. Verificando base de conhecimento...")

        # Verificar se dados contaminados ainda existem
        contaminated_searches = [
            "STILL YOU",
            "Heaven Race",
            "Liu escreveu",
            "A floresta sombria Liu"
        ]

        for search_term in contaminated_searches:
            results = training_service.search_knowledge_base(
                search_term,
                threshold=0.3,
                max_results=3
            )

            if results:
                self.stdout.write(f"   ⚠️  Dados contaminados encontrados para '{search_term}':")
                for item, score in results:
                    self.stdout.write(f"      - {item.question[:50]}... (score: {score:.3f})")
            else:
                self.stdout.write(f"   ✅ Sem dados contaminados para '{search_term}'")

        # 4. Teste do usuário
        self.stdout.write(f"\n📋 4. Obtendo usuário de teste (ID: {user_id})...")
        try:
            user = User.objects.get(id=user_id)
            self.stdout.write(f"   ✅ Usuário encontrado: {user.username}")
        except User.DoesNotExist:
            self.stdout.write(f"   ❌ Usuário ID {user_id} não encontrado")
            user = None

        # 5. Teste de contexto crítico
        self.stdout.write("\n📋 5. TESTE CRÍTICO DO CONTEXTO")
        self.stdout.write("-" * 40)

        # Limpar contexto antes do teste
        if user:
            chatbot.clear_user_context(user)

        test_sequence = [
            "Fale sobre Harry Potter",
            "Quem escreveu?",
            "Agora fale sobre J.K. Rowling",
            "Quais livros ela escreveu?"
        ]

        for i, message in enumerate(test_sequence, 1):
            self.stdout.write(f"\n🎯 Teste {i}: '{message}'")

            try:
                response, source = chatbot.get_response(message, user)

                self.stdout.write(f"   📤 Resposta: {response[:100]}...")
                self.stdout.write(f"   📍 Fonte: {source}")

                # Verificações específicas
                response_lower = response.lower()

                if i == 1:  # "Fale sobre Harry Potter"
                    if "harry potter" in response_lower:
                        self.stdout.write("   ✅ Resposta sobre Harry Potter correta")
                    else:
                        self.stdout.write("   ⚠️  Resposta não menciona Harry Potter")

                elif i == 2:  # "Quem escreveu?"
                    if "j.k. rowling" in response_lower or "rowling" in response_lower:
                        self.stdout.write("   ✅ Contexto funcionando - J.K. Rowling identificada")
                    elif "still you" in response_lower or "heaven race" in response_lower:
                        self.stdout.write("   ❌ BUG CRÍTICO: Dados contaminados retornados!")
                    else:
                        self.stdout.write(f"   ⚠️  Resposta inesperada: {response[:50]}...")

                elif i == 3:  # "Agora fale sobre J.K. Rowling"
                    if "rowling" in response_lower or "j.k." in response_lower:
                        self.stdout.write("   ✅ Mudança de contexto funcionando")
                    else:
                        self.stdout.write("   ⚠️  Mudança de contexto pode ter problemas")

                elif i == 4:  # "Quais livros ela escreveu?"
                    if "harry potter" in response_lower and "rowling" in response_lower:
                        self.stdout.write("   ✅ Contexto sobre autora funcionando")
                    elif "liu" in response_lower or "floresta sombria" in response_lower:
                        self.stdout.write("   ❌ BUG CRÍTICO: Contexto incorreto (Liu/Floresta)!")
                    else:
                        self.stdout.write(f"   ⚠️  Resposta inesperada: {response[:50]}...")

            except Exception as e:
                self.stdout.write(f"   ❌ ERRO: {str(e)}")

        # 6. Verificar contexto atual
        self.stdout.write("\n📋 6. Estado do contexto após teste...")
        if user:
            context = chatbot.get_user_context(user)
            self.stdout.write(f"   📚 Entidades extraídas: {context.entities}")
            self.stdout.write(f"   🎯 Último tópico: {context.last_topic}")
            self.stdout.write(f"   ❓ Último tipo de pergunta: {context.last_question_type}")
            self.stdout.write(f"   💬 Mensagens no histórico: {len(context.conversation_history)}")

        # 7. Teste específico da base de conhecimento
        self.stdout.write("\n📋 7. Teste direto da base de conhecimento...")

        direct_tests = [
            "Quem escreveu Harry Potter",
            "J.K. Rowling livros",
            "autor Harry Potter"
        ]

        for query in direct_tests:
            results = training_service.search_knowledge_base(query, threshold=0.5, max_results=3)
            self.stdout.write(f"\n   🔍 Busca: '{query}'")

            if results:
                for i, (item, score) in enumerate(results, 1):
                    self.stdout.write(f"      {i}. {item.question} -> {item.answer[:60]}... (score: {score:.3f})")
            else:
                self.stdout.write("      ❌ Nenhum resultado encontrado")

        # 8. Resumo final
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("📊 RESUMO DA VERIFICAÇÃO")
        self.stdout.write("=" * 60)

        self.stdout.write("\n✅ Itens Verificados:")
        self.stdout.write("   - Métodos corrigidos presentes no código")
        self.stdout.write("   - Base de conhecimento verificada")
        self.stdout.write("   - Sequência crítica de contexto testada")
        self.stdout.write("   - Busca direta na base testada")

        self.stdout.write("\n💡 Próximos passos se houver problemas:")
        self.stdout.write("   1. Reiniciar o servidor Django")
        self.stdout.write("   2. Executar limpeza adicional da base")
        self.stdout.write("   3. Verificar se há cache Python ativo")
        self.stdout.write("   4. Atualizar embeddings novamente")

        self.stdout.write("\n🎯 Para limpeza da base execute:")
        self.stdout.write("   python manage.py clean_knowledge_base")

        self.stdout.write("\n🔄 Para atualizar embeddings execute:")
        self.stdout.write("   python manage.py update_embeddings")

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("🏁 VERIFICAÇÃO CONCLUÍDA")
        self.stdout.write("=" * 60)
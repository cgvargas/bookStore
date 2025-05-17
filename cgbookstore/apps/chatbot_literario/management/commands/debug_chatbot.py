from django.core.management.base import BaseCommand
import inspect
import traceback
from cgbookstore.apps.chatbot_literario.services.chatbot_service import chatbot
from cgbookstore.apps.chatbot_literario.services.training_service import training_service
from cgbookstore.apps.chatbot_literario.models import KnowledgeItem


class Command(BaseCommand):
    help = 'Debug completo do chatbot para identificar problemas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--query',
            type=str,
            default='Como está o tempo hoje?',
            help='Mensagem de teste para o chatbot',
        )

    def handle(self, *args, **options):
        query = options['query']

        self.stdout.write(self.style.WARNING(f"\n{'=' * 50}"))
        self.stdout.write(self.style.WARNING(f"DIAGNÓSTICO COMPLETO DO CHATBOT"))
        self.stdout.write(self.style.WARNING(f"{'=' * 50}\n"))

        # Parte 1: Verificar estrutura do chatbot
        self.stdout.write(self.style.HTTP_INFO("\n1. VERIFICANDO ESTRUTURA DO CHATBOT"))
        self.verify_chatbot_structure()

        # Parte 2: Verificar base de conhecimento
        self.stdout.write(self.style.HTTP_INFO("\n2. VERIFICANDO BASE DE CONHECIMENTO"))
        self.verify_knowledge_base()

        # Parte 3: Testar busca na base de conhecimento
        self.stdout.write(self.style.HTTP_INFO("\n3. TESTANDO BUSCA NA BASE DE CONHECIMENTO"))
        self.test_knowledge_search(query)

        # Parte 4: Testar processamento completo de mensagem
        self.stdout.write(self.style.HTTP_INFO("\n4. TESTANDO PROCESSAMENTO COMPLETO DE MENSAGEM"))
        self.test_full_message_processing(query)

    def verify_chatbot_structure(self):
        """Verifica a estrutura e métodos do chatbot."""
        try:
            self.stdout.write("Chatbot inicializado: " + str(chatbot.initialized))
            self.stdout.write("Métodos do chatbot:")

            # Listar métodos disponíveis
            methods = inspect.getmembers(chatbot, predicate=inspect.ismethod)
            for name, method in methods:
                if not name.startswith('_') or name == '__init__':
                    self.stdout.write(f"  - {name}")

            # Verificar serviço de treinamento
            self.stdout.write("\nServiço de treinamento inicializado: " + str(training_service.initialized))
            self.stdout.write("Modelo de embeddings disponível: " + str(training_service.embedding_model is not None))

            # Inicializar se necessário
            if not chatbot.initialized:
                chatbot.initialize()
                self.stdout.write("Chatbot inicializado agora: " + str(chatbot.initialized))

            if not training_service.initialized:
                training_service.initialize()
                self.stdout.write("Serviço de treinamento inicializado agora: " + str(training_service.initialized))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"ERRO ao verificar estrutura do chatbot: {str(e)}"))
            self.stdout.write(traceback.format_exc())

    def verify_knowledge_base(self):
        """Verifica o estado da base de conhecimento."""
        try:
            # Obter estatísticas
            total_items = KnowledgeItem.objects.count()
            active_items = KnowledgeItem.objects.filter(active=True).count()
            items_with_embeddings = KnowledgeItem.objects.exclude(embedding__isnull=True).exclude(embedding={}).count()

            self.stdout.write(f"Total de itens: {total_items}")
            self.stdout.write(f"Itens ativos: {active_items}")
            self.stdout.write(f"Itens com embeddings: {items_with_embeddings}")

            # Verificar formato dos embeddings
            sample_items = KnowledgeItem.objects.exclude(embedding__isnull=True).exclude(embedding={})[:5]

            if sample_items:
                self.stdout.write("\nAmostra de embeddings:")
                for item in sample_items:
                    embedding_type = type(item.embedding).__name__
                    embedding_length = len(item.embedding) if hasattr(item.embedding, '__len__') else 'N/A'
                    self.stdout.write(f"  - ID: {item.id}, Tipo: {embedding_type}, Tamanho: {embedding_length}")

            # Verificar itens sem embedding
            no_embedding_items = KnowledgeItem.objects.filter(embedding__isnull=True)[:5]
            if no_embedding_items:
                self.stdout.write("\nAmostra de itens sem embedding:")
                for item in no_embedding_items:
                    self.stdout.write(f"  - ID: {item.id}, Pergunta: {item.question[:30]}...")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"ERRO ao verificar base de conhecimento: {str(e)}"))
            self.stdout.write(traceback.format_exc())

    def test_knowledge_search(self, query):
        """Testa a busca na base de conhecimento."""
        try:
            self.stdout.write(f"Buscando por: '{query}'")

            # Chamar a função de busca diretamente
            search_results = training_service.search_knowledge_base(query)

            self.stdout.write(f"Resultados encontrados: {len(search_results)}")

            if search_results:
                self.stdout.write("\nMelhores correspondências:")
                for i, (item, score) in enumerate(search_results):
                    self.stdout.write(f"{i + 1}. Score: {score:.4f}")
                    self.stdout.write(f"   Pergunta: {item.question}")
                    self.stdout.write(f"   Resposta: {item.answer}")
                    self.stdout.write(f"   Tipo de item: {type(item).__name__}")
                    self.stdout.write(f"   ID: {item.id}")

                # Testar acesso ao melhor resultado
                try:
                    best_item, best_score = search_results[0]
                    self.stdout.write(f"\nAcesso ao melhor resultado - OK")
                    self.stdout.write(f"Melhor resposta: {best_item.answer}")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"ERRO ao acessar melhor resultado: {str(e)}"))
            else:
                self.stdout.write("Nenhum resultado encontrado.")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"ERRO ao testar busca: {str(e)}"))
            self.stdout.write(traceback.format_exc())

    def test_full_message_processing(self, query):
        """Testa o processamento completo de uma mensagem."""
        try:
            self.stdout.write(f"Processando mensagem: '{query}'")

            # Chamar o método get_response
            response, source = chatbot.get_response(query)

            self.stdout.write(f"Resposta: '{response}'")
            self.stdout.write(f"Fonte: {source}")

            # Verificar funcionamento completo
            self.stdout.write(self.style.SUCCESS("\nTeste de processamento completo - OK"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"ERRO ao processar mensagem: {str(e)}"))
            self.stdout.write(traceback.format_exc())
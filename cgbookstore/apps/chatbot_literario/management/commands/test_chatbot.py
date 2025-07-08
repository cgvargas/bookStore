from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from cgbookstore.apps.chatbot_literario.services.chatbot_service import chatbot
from cgbookstore.apps.chatbot_literario.models import KnowledgeItem
from colorama import init, Fore, Style
import sys

# Inicializar colorama para cores no terminal
init()


class Command(BaseCommand):
    help = 'Testa o funcionamento do chatbot com conversas simuladas ou interativas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interactive',
            action='store_true',
            help='Inicia o modo interativo para conversar com o chatbot',
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Username do usuário para simular (opcional)',
        )
        parser.add_argument(
            '--scenario',
            type=str,
            choices=['all', 'basic', 'books', 'navigation', 'context'],
            default='all',
            help='Cenário de teste específico a executar',
        )

    def handle(self, *args, **options):
        # Inicializar o chatbot
        self.stdout.write("Inicializando chatbot...")
        chatbot.initialize()
        self.stdout.write(self.style.SUCCESS("✓ Chatbot inicializado com sucesso!"))

        # Verificar base de conhecimento
        knowledge_count = KnowledgeItem.objects.count()
        if knowledge_count == 0:
            self.stdout.write(self.style.WARNING(
                "\n⚠️  Base de conhecimento vazia! Execute primeiro:"
            ))
            self.stdout.write(self.style.WARNING(
                "   python manage.py populate_knowledge_base"
            ))
            self.stdout.write(self.style.WARNING(
                "   ou python manage.py populate_knowledge_base --json sample_knowledge.json\n"
            ))
        else:
            self.stdout.write(f"\n📚 Base de conhecimento: {knowledge_count} itens\n")

        # Obter usuário se especificado
        user = None
        if options['user']:
            try:
                user = User.objects.get(username=options['user'])
                self.stdout.write(f"👤 Usando usuário: {user.username}\n")
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"Usuário '{options['user']}' não encontrado. Continuando como anônimo.\n"))

        if options['interactive']:
            self.interactive_mode(user)
        else:
            self.test_scenarios(options['scenario'], user)

    def print_bot_response(self, response, source):
        """Imprime a resposta do bot com formatação colorida."""
        self.stdout.write(f"\n{Fore.CYAN}🤖 Bot:{Style.RESET_ALL} {response}")
        self.stdout.write(f"{Fore.YELLOW}   [Fonte: {source}]{Style.RESET_ALL}")

    def print_user_message(self, message):
        """Imprime a mensagem do usuário com formatação."""
        self.stdout.write(f"\n{Fore.GREEN}👤 Você:{Style.RESET_ALL} {message}")

    def test_scenarios(self, scenario, user):
        """Executa cenários de teste específicos ou todos."""
        if scenario == 'all' or scenario == 'basic':
            self.test_basic_conversation(user)

        if scenario == 'all' or scenario == 'books':
            self.test_book_queries(user)

        if scenario == 'all' or scenario == 'navigation':
            self.test_navigation_queries(user)

        if scenario == 'all' or scenario == 'context':
            self.test_contextual_queries(user)

    def test_basic_conversation(self, user):
        """Testa conversas básicas (saudação, ajuda, despedida)."""
        self.stdout.write(f"\n{Fore.MAGENTA}--- Teste: Conversação Básica ---{Style.RESET_ALL}")

        messages = [
            "Olá!",
            "O que você pode fazer?",
            "Obrigado!",
            "Tchau!"
        ]

        for message in messages:
            self.print_user_message(message)
            response, source = chatbot.get_response(message, user)
            self.print_bot_response(response, source)

    def test_book_queries(self, user):
        """Testa perguntas sobre livros."""
        self.stdout.write(f"\n\n{Fore.MAGENTA}--- Teste: Consultas sobre Livros ---{Style.RESET_ALL}")

        # Limpar contexto para nova conversa
        chatbot.clear_user_context(user)

        messages = [
            "Quem escreveu O Senhor dos Anéis?",
            "Me fale sobre 1984",
            "Pode me recomendar livros de fantasia?",
            "Quais livros George Orwell escreveu?"
        ]

        for message in messages:
            self.print_user_message(message)
            response, source = chatbot.get_response(message, user)
            self.print_bot_response(response, source)

    def test_navigation_queries(self, user):
        """Testa perguntas sobre navegação no site."""
        self.stdout.write(f"\n\n{Fore.MAGENTA}--- Teste: Navegação no Site ---{Style.RESET_ALL}")

        # Limpar contexto para nova conversa
        chatbot.clear_user_context(user)

        messages = [
            "Como encontro meus livros favoritos?",
            "Onde vejo os livros que estou lendo?",
            "Como adiciono um livro ao carrinho?",
            "Como faço para avaliar um livro?"
        ]

        for message in messages:
            self.print_user_message(message)
            response, source = chatbot.get_response(message, user)
            self.print_bot_response(response, source)

    def test_contextual_queries(self, user):
        """Testa perguntas contextuais encadeadas."""
        self.stdout.write(f"\n\n{Fore.MAGENTA}--- Teste: Perguntas Contextuais ---{Style.RESET_ALL}")

        # Limpar contexto para nova conversa
        chatbot.clear_user_context(user)

        messages = [
            "Fale sobre O Hobbit",
            "Quem escreveu?",
            "E quando foi publicado?",
            "Quem escreveu Dom Casmurro?",
            "E quando foi publicado?",
            "O autor escreveu outros livros?"
        ]

        for message in messages:
            self.print_user_message(message)
            response, source = chatbot.get_response(message, user)
            self.print_bot_response(response, source)

    def interactive_mode(self, user):
        """Modo interativo para conversar com o chatbot em tempo real."""
        self.stdout.write(f"\n{Fore.MAGENTA}{'=' * 60}")
        self.stdout.write("MODO INTERATIVO - CHATBOT LITERÁRIO")
        self.stdout.write(f"{'=' * 60}{Style.RESET_ALL}\n")
        self.stdout.write(f"{Fore.YELLOW}Digite 'sair' para encerrar a conversa")
        self.stdout.write(f"Digite 'limpar' para limpar o contexto da conversa{Style.RESET_ALL}\n")

        while True:
            try:
                # Receber mensagem do usuário
                message = input(f"\n{Fore.GREEN}👤 Você: {Style.RESET_ALL}")

                if message.lower() in ['sair', 'exit', 'quit']:
                    self.stdout.write(f"\n{Fore.MAGENTA}Encerrando conversa... Até mais!{Style.RESET_ALL}")
                    break

                if message.lower() == 'limpar':
                    chatbot.clear_user_context(user)
                    self.stdout.write(f"{Fore.YELLOW}✓ Contexto da conversa limpo!{Style.RESET_ALL}")
                    continue

                # Obter resposta do chatbot
                response, source = chatbot.get_response(message, user)

                # Exibir resposta
                self.stdout.write(f"{Fore.CYAN}🤖 Bot:{Style.RESET_ALL} {response}")
                self.stdout.write(f"{Fore.YELLOW}   [Fonte: {source}]{Style.RESET_ALL}")

            except KeyboardInterrupt:
                self.stdout.write(f"\n\n{Fore.MAGENTA}Conversa interrompida. Até mais!{Style.RESET_ALL}")
                break
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"\nErro: {str(e)}"))
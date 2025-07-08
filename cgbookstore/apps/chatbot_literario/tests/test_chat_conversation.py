import os
import sys
import django

# Configurar o Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookstore.settings')
django.setup()

from cgbookstore.apps.chatbot_literario.services.chatbot_service import chatbot
from django.contrib.auth.models import User
from colorama import init, Fore, Style

# Inicializar colorama para cores no terminal
init()


def print_bot_response(response, source):
    """Imprime a resposta do bot com formatação colorida."""
    print(f"\n{Fore.CYAN}🤖 Bot:{Style.RESET_ALL} {response}")
    print(f"{Fore.YELLOW}   [Fonte: {source}]{Style.RESET_ALL}")


def print_user_message(message):
    """Imprime a mensagem do usuário com formatação."""
    print(f"\n{Fore.GREEN}👤 Você:{Style.RESET_ALL} {message}")


def simulate_conversation():
    """Simula uma conversa completa com o chatbot."""
    print(f"{Fore.MAGENTA}{'=' * 60}")
    print("TESTE DE CONVERSA DO CHATBOT LITERÁRIO")
    print(f"{'=' * 60}{Style.RESET_ALL}\n")

    # Inicializar o chatbot
    print(f"{Fore.YELLOW}Inicializando chatbot...{Style.RESET_ALL}")
    chatbot.initialize()
    print(f"{Fore.GREEN}✓ Chatbot inicializado com sucesso!{Style.RESET_ALL}\n")

    # Simular usuário (opcional - pode ser None para usuário anônimo)
    user = None  # Ou User.objects.first() se quiser usar um usuário real

    # Cenário 1: Saudação e pedido de ajuda
    print(f"\n{Fore.MAGENTA}--- Cenário 1: Saudação e Ajuda ---{Style.RESET_ALL}")

    conversation_1 = [
        "Olá!",
        "O que você pode fazer?",
        "Tchau!"
    ]

    for message in conversation_1:
        print_user_message(message)
        response, source = chatbot.get_response(message, user)
        print_bot_response(response, source)

    # Cenário 2: Perguntas sobre livros específicos
    print(f"\n\n{Fore.MAGENTA}--- Cenário 2: Perguntas sobre Livros ---{Style.RESET_ALL}")

    conversation_2 = [
        "Quem escreveu O Senhor dos Anéis?",
        "E quando foi publicado?",
        "E O Hobbit?",
        "Quem é o autor?"
    ]

    # Limpar contexto para nova conversa
    chatbot.clear_user_context(user)

    for message in conversation_2:
        print_user_message(message)
        response, source = chatbot.get_response(message, user)
        print_bot_response(response, source)

    # Cenário 3: Recomendações e navegação
    print(f"\n\n{Fore.MAGENTA}--- Cenário 3: Recomendações e Navegação ---{Style.RESET_ALL}")

    conversation_3 = [
        "Pode me recomendar um livro de fantasia?",
        "Como posso encontrar mais livros no site?",
        "Onde vejo meus favoritos?"
    ]

    # Limpar contexto para nova conversa
    chatbot.clear_user_context(user)

    for message in conversation_3:
        print_user_message(message)
        response, source = chatbot.get_response(message, user)
        print_bot_response(response, source)

    # Cenário 4: Perguntas contextuais complexas
    print(f"\n\n{Fore.MAGENTA}--- Cenário 4: Contexto e Perguntas Encadeadas ---{Style.RESET_ALL}")

    conversation_4 = [
        "Fale sobre 1984",
        "Quem escreveu?",
        "E quando foi publicado?",
        "O autor escreveu outros livros?",
        "Me fale sobre A Revolução dos Bichos",
        "E o autor?"
    ]

    # Limpar contexto para nova conversa
    chatbot.clear_user_context(user)

    for message in conversation_4:
        print_user_message(message)
        response, source = chatbot.get_response(message, user)
        print_bot_response(response, source)

    # Cenário 5: Teste de resiliência
    print(f"\n\n{Fore.MAGENTA}--- Cenário 5: Teste de Resiliência ---{Style.RESET_ALL}")

    conversation_5 = [
        "asdkfjalskdfj",
        "????",
        "Me ajuda",
        "Quero comprar um livro mas não sei qual",
        "Obrigado!"
    ]

    # Limpar contexto para nova conversa
    chatbot.clear_user_context(user)

    for message in conversation_5:
        print_user_message(message)
        response, source = chatbot.get_response(message, user)
        print_bot_response(response, source)

    print(f"\n\n{Fore.MAGENTA}{'=' * 60}")
    print("TESTE CONCLUÍDO")
    print(f"{'=' * 60}{Style.RESET_ALL}\n")


def interactive_mode():
    """Modo interativo para conversar com o chatbot em tempo real."""
    print(f"{Fore.MAGENTA}{'=' * 60}")
    print("MODO INTERATIVO - CHATBOT LITERÁRIO")
    print(f"{'=' * 60}{Style.RESET_ALL}\n")
    print(f"{Fore.YELLOW}Digite 'sair' para encerrar a conversa{Style.RESET_ALL}\n")

    # Inicializar o chatbot
    print(f"{Fore.YELLOW}Inicializando chatbot...{Style.RESET_ALL}")
    chatbot.initialize()
    print(f"{Fore.GREEN}✓ Chatbot inicializado!{Style.RESET_ALL}\n")

    user = None

    while True:
        try:
            # Receber mensagem do usuário
            message = input(f"\n{Fore.GREEN}👤 Você: {Style.RESET_ALL}")

            if message.lower() in ['sair', 'exit', 'quit']:
                print(f"\n{Fore.MAGENTA}Encerrando conversa... Até mais!{Style.RESET_ALL}")
                break

            # Obter resposta do chatbot
            response, source = chatbot.get_response(message, user)

            # Exibir resposta
            print(f"{Fore.CYAN}🤖 Bot:{Style.RESET_ALL} {response}")
            print(f"{Fore.YELLOW}   [Fonte: {source}]{Style.RESET_ALL}")

        except KeyboardInterrupt:
            print(f"\n\n{Fore.MAGENTA}Conversa interrompida. Até mais!{Style.RESET_ALL}")
            break
        except Exception as e:
            print(f"\n{Fore.RED}Erro: {str(e)}{Style.RESET_ALL}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        # Modo interativo
        interactive_mode()
    else:
        # Modo de simulação automática
        simulate_conversation()

        # Perguntar se deseja entrar no modo interativo
        print(f"\n{Fore.YELLOW}Deseja iniciar o modo interativo? (s/n): {Style.RESET_ALL}", end="")
        choice = input().lower()
        if choice == 's':
            print()
            interactive_mode()
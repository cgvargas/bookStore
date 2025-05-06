from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging

from .models import Conversation, Message
from .services.chatbot_service import chatbot
from .services.training_service import training_service

logger = logging.getLogger(__name__)


@login_required
def chatbot_view(request):
    """Renderiza a página principal do chatbot."""
    # Obter ou criar uma conversa para o usuário
    conversation, created = Conversation.objects.get_or_create(
        user=request.user,
        defaults={'user': request.user}
    )

    # Obter histórico de mensagens
    messages = conversation.messages.all()

    context = {
        'conversation': conversation,
        'messages': messages,
    }

    return render(request, 'chatbot_literario/chat.html', context)


@login_required
def chatbot_widget(request):
    """Renderiza apenas o widget do chatbot para inclusão em outras páginas."""
    # Obter ou criar uma conversa para o usuário
    conversation, created = Conversation.objects.get_or_create(
        user=request.user,
        defaults={'user': request.user}
    )

    # Obter histórico recente limitado
    messages = conversation.messages.all()[:10]

    context = {
        'conversation': conversation,
        'messages': messages,
    }

    return render(request, 'chatbot_literario/widget.html', context)


@login_required
@csrf_exempt
def chatbot_message(request):
    """Endpoint para receber e processar mensagens do chatbot."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    try:
        # Carregar dados do corpo da requisição
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()

        if not user_message:
            return JsonResponse({'error': 'Mensagem vazia'}, status=400)

        # Obter ou criar conversa para o usuário
        conversation, created = Conversation.objects.get_or_create(
            user=request.user,
            defaults={'user': request.user}
        )

        # Salvar mensagem do usuário
        Message.objects.create(
            conversation=conversation,
            sender='user',
            content=user_message
        )

        # Respostas diretas para botões de sugestão
        if user_message.lower() == "recomende livros":
            bot_response = "Com base em nosso catálogo, posso recomendar alguns livros populares: 'O Hobbit' para fantasia, '1984' para ficção distópica, 'O Nome do Vento' para fantasia épica, e 'Orgulho e Preconceito' para clássicos. Qual gênero te interessa mais?"
        elif user_message.lower() == "como funciona?":
            bot_response = "Sou um assistente literário projetado para ajudar com recomendações de livros, informações sobre autores e navegação no site. Você pode me perguntar sobre gêneros literários, encontrar funcionalidades específicas no site, ou obter sugestões personalizadas."
        elif user_message.lower() == "meus favoritos":
            bot_response = "Seus livros favoritos podem ser encontrados na sua página de perfil. Basta clicar em 'Perfil' no menu superior e você verá a seção 'Favoritos' com todos os livros que você marcou."
        else:
            # Processar a mensagem do usuário
            try:
                # Verificar base de conhecimento primeiro - ABORDAGEM SEGURA SEM VERIFICAR 'initialized'
                knowledge_results = []
                try:
                    # Usar try-except em vez de verificar o atributo
                    knowledge_results = training_service.search_knowledge_base(user_message)
                except Exception as e:
                    logger.error(f"Erro ao buscar na base de conhecimento: {str(e)}")
                    knowledge_results = []

                # Se encontrou resultados relevantes na base de conhecimento
                if knowledge_results and len(knowledge_results) > 0 and knowledge_results[0][1] > 0.7:
                    bot_response = knowledge_results[0][0]['answer']
                    logger.info(f"Resposta da base de conhecimento para: {user_message}")
                else:
                    # Caso contrário, usar o modelo DialoGPT
                    bot_response, _ = chatbot.get_response(user_message, user=request.user)
                    logger.info(f"Resposta do modelo para: {user_message}")

            except Exception as e:
                logger.error(f"Erro ao processar mensagem: {str(e)}")
                # Resposta de fallback em caso de erro
                bot_response = "Desculpe, estou enfrentando algumas dificuldades no momento. Poderia tentar novamente mais tarde?"

        # Salvar resposta do chatbot
        bot_message = Message.objects.create(
            conversation=conversation,
            sender='bot',
            content=bot_response
        )

        # Tentar registrar a conversa para treinamento futuro - ABORDAGEM SEGURA
        try:
            # Usar try-except em vez de verificar o atributo
            training_service.add_conversation(user_message, bot_response)
        except Exception as e:
            logger.error(f"Erro ao registrar conversa: {str(e)}")

        # Formatar horário corretamente para a resposta
        formatted_time = bot_message.timestamp.strftime('%H:%M')

        return JsonResponse({
            'response': bot_response,
            'timestamp': formatted_time,
            'message_id': bot_message.id
        })

    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {str(e)}")
        return JsonResponse({'error': 'Erro interno do servidor'}, status=500)


@login_required
@csrf_exempt
def chatbot_feedback(request):
    """Endpoint para receber feedback sobre respostas do chatbot."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    try:
        data = json.loads(request.body)
        message_id = data.get('message_id')
        helpful = data.get('helpful', False)
        comment = data.get('comment', '')

        if not message_id:
            return JsonResponse({'error': 'ID da mensagem não fornecido'}, status=400)

        # Obter mensagem
        try:
            message = Message.objects.get(id=message_id, sender='bot')
        except Message.DoesNotExist:
            return JsonResponse({'error': 'Mensagem não encontrada'}, status=404)

        # Verificar se o usuário tem acesso à conversa
        if message.conversation.user != request.user:
            return JsonResponse({'error': 'Acesso negado'}, status=403)

        # Obter mensagem anterior do usuário
        try:
            user_message = Message.objects.filter(
                conversation=message.conversation,
                sender='user',
                timestamp__lt=message.timestamp
            ).latest('timestamp')

            # Adicionar feedback ao serviço de treinamento
            feedback_data = {
                'helpful': helpful,
                'comment': comment
            }

            # Tentar registrar o feedback
            try:
                if hasattr(training_service, 'conversation_data'):
                    # Localizar a conversa nos dados de treinamento
                    for i, conv in enumerate(training_service.conversation_data):
                        if (conv.get('user_input') == user_message.content and
                                conv.get('bot_response') == message.content):
                            if hasattr(training_service, 'add_feedback'):
                                training_service.add_feedback(i, feedback_data)
                            break
            except Exception as e:
                logger.error(f"Erro ao salvar feedback: {str(e)}")

            return JsonResponse({'success': True})

        except Exception as e:
            logger.error(f"Erro ao processar feedback: {str(e)}")
            return JsonResponse({'error': 'Erro ao processar feedback'}, status=500)

    except Exception as e:
        logger.error(f"Erro ao processar feedback: {str(e)}")
        return JsonResponse({'error': 'Erro interno do servidor'}, status=500)
import json
import traceback
import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.conf import settings

from .models import Conversation, Message, ConversationFeedback
from .services.chatbot_service import chatbot

logger = logging.getLogger(__name__)

# Cache de transações recentes para evitar duplicações
recent_transactions = {}


@login_required
def chatbot_view(request):
    """Renderiza a página principal do chatbot."""
    # Obter ou criar conversa para o usuário atual
    conversation, created = Conversation.objects.get_or_create(
        user=request.user,
        defaults={'started_at': timezone.now()}
    )

    # Obter mensagens da conversa
    messages = Message.objects.filter(conversation=conversation)

    return render(request, 'chatbot_literario/chat.html', {
        'messages': messages
    })


def chatbot_widget(request):
    """Renderiza o widget do chatbot."""
    # Se o usuário estiver autenticado, obter mensagens da conversa
    messages = []
    if request.user.is_authenticated:
        conversation, created = Conversation.objects.get_or_create(
            user=request.user,
            defaults={'started_at': timezone.now()}
        )
        messages = Message.objects.filter(conversation=conversation)

    return render(request, 'chatbot_literario/widget.html', {
        'messages': messages
    })


@csrf_exempt
def chatbot_message(request):
    """
    Endpoint para processamento de mensagens do chatbot.
    Recebe mensagem do usuário e retorna resposta.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    try:
        # Obter dados da requisição
        data = json.loads(request.body)
        message_text = data.get('message', '').strip()
        transaction_id = data.get('transaction_id', '')

        # Verificar se é uma mensagem vazia
        if not message_text:
            return JsonResponse({'error': 'Mensagem vazia'}, status=400)

        # Verificar por mensagens duplicadas (proteção contra cliques duplos)
        if transaction_id and transaction_id in recent_transactions:
            logger.warning(f"Mensagem duplicada detectada: {message_text[:20]}...")
            return JsonResponse({'error': 'Mensagem duplicada'}, status=409)

        # Armazenar transação recente
        if transaction_id:
            recent_transactions[transaction_id] = True
            # Limitar tamanho do cache
            if len(recent_transactions) > 100:
                # Remover itens mais antigos
                keys = list(recent_transactions.keys())
                for key in keys[:50]:
                    recent_transactions.pop(key, None)

        # Obter usuário (autenticado ou anônimo)
        user = request.user if request.user.is_authenticated else None

        # Obter ou criar conversa
        conversation = None
        if user:
            conversation, created = Conversation.objects.get_or_create(
                user=user,
                defaults={'started_at': timezone.now()}
            )
            # Atualizar timestamp da conversa
            if not created:
                conversation.updated_at = timezone.now()
                conversation.save()

        # Adicionar mensagem do usuário ao banco de dados
        user_message = None
        if conversation:
            user_message = Message.objects.create(
                conversation=conversation,
                sender='user',
                content=message_text
            )

        # ADICIONAR DEBUG AQUI - Print detalhado das estruturas
        print("\n==== DEBUG: Processamento de Mensagem ====")
        print(f"Mensagem do usuário: {message_text}")

        # Obter resposta do chatbot
        try:
            response_text, source = chatbot.get_response(message_text, user=user)

            print(f"Resposta obtida do chatbot: {response_text}")
            print(f"Fonte da resposta: {source}")

        except Exception as e:
            print(f"ERRO DETALHADO na chamada do chatbot: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            raise

        # Adicionar resposta do bot ao banco de dados
        bot_message = None
        if conversation:
            bot_message = Message.objects.create(
                conversation=conversation,
                sender='bot',
                content=response_text
            )

        # Formatar resposta para o frontend
        response_data = {
            'response': response_text,
            'timestamp': timezone.now().strftime('%H:%M')
        }

        # Adicionar ID da mensagem para feedback (se disponível)
        if bot_message:
            response_data['message_id'] = bot_message.id

        return JsonResponse(response_data)

    except json.JSONDecodeError:
        logger.error("Erro ao decodificar JSON da requisição")
        return JsonResponse({'error': 'Formato de requisição inválido'}, status=400)
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {str(e)}")
        return JsonResponse({'error': 'Erro interno do servidor'}, status=500)


@csrf_exempt
def chatbot_feedback(request):
    """
    Endpoint para receber feedback sobre respostas do chatbot.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    try:
        # Obter dados da requisição
        data = json.loads(request.body)
        message_id = data.get('message_id')
        helpful = data.get('helpful', False)
        comment = data.get('comment', '')

        # Verificar se message_id foi fornecido
        if not message_id:
            return JsonResponse({'error': 'ID da mensagem não fornecido'}, status=400)

        # Obter mensagem
        try:
            message = Message.objects.get(id=message_id, sender='bot')
        except Message.DoesNotExist:
            return JsonResponse({'error': 'Mensagem não encontrada'}, status=404)

        # Verificar se já existe feedback para esta mensagem
        feedback, created = ConversationFeedback.objects.get_or_create(
            message=message,
            defaults={
                'helpful': helpful,
                'comment': comment
            }
        )

        # Se feedback já existia, atualizar
        if not created:
            feedback.helpful = helpful
            feedback.comment = comment
            feedback.save()

        return JsonResponse({'success': True})

    except json.JSONDecodeError:
        logger.error("Erro ao decodificar JSON da requisição de feedback")
        return JsonResponse({'error': 'Formato de requisição inválido'}, status=400)
    except Exception as e:
        logger.error(f"Erro ao processar feedback: {str(e)}")
        return JsonResponse({'error': 'Erro interno do servidor'}, status=500)
# cgbookstore/apps/chatbot_literario/views.py

import json
import logging
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.utils import timezone

from .models import Conversation, Message, ConversationFeedback
#Importa a instância do chatbot criada no __init__.py
from .services import functional_chatbot

logger = logging.getLogger(__name__)


# =============================================================================
# Funções Auxiliares
# =============================================================================

def get_user_favorites(user):
    """Obtém livros favoritos do usuário"""
    try:
        from cgbookstore.apps.core.models import UserBookShelf
        favorites = UserBookShelf.objects.filter(user=user, shelf_type='favorito').select_related('book')[:5]
        return [{'titulo': shelf.book.titulo, 'autor': shelf.book.autor, 'capa_url': shelf.book.get_capa_url()} for
                shelf in favorites]
    except Exception:
        return []


def get_user_reading_history(user):
    """Obtém histórico de leitura do usuário"""
    try:
        from cgbookstore.apps.core.models import UserBookShelf
        history = UserBookShelf.objects.filter(user=user, shelf_type__in=['lido', 'lendo']).select_related(
            'book').order_by('-added_at')[:10]
        return [{'titulo': shelf.book.titulo, 'autor': shelf.book.autor, 'status': shelf.get_shelf_type_display(),
                 'data': shelf.added_at.strftime('%d/%m/%Y')} for shelf in history]
    except Exception:
        return []


def get_user_preferences(user):
    """Obtém preferências literárias do usuário"""
    try:
        from cgbookstore.apps.core.models import UserBookShelf
        user_books = UserBookShelf.objects.filter(user=user, shelf_type__in=['favorito', 'lido']).select_related(
            'book')[:20]
        genres = {}
        for shelf in user_books:
            if shelf.book.genero:
                genres[shelf.book.genero] = genres.get(shelf.book.genero, 0) + 1
        preferred_genres = sorted(genres.items(), key=lambda x: x[1], reverse=True)[:3]
        return {'generos_preferidos': [g for g, c in preferred_genres]}
    except Exception:
        return {}


# =============================================================================
# Views Principais
# =============================================================================

class ChatbotView(LoginRequiredMixin, TemplateView):
    """View principal do chatbot literário (página completa)"""
    template_name = 'chatbot_literario/chat.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # ✅ CORREÇÃO: Busca o histórico de conversas diretamente do banco de dados.
        recent_conversations = Conversation.objects.filter(user=user).order_by('-updated_at')[:5]

        context.update({
            'page_title': 'Chatbot Literário',
            'recent_conversations': recent_conversations,
            'favorites': get_user_favorites(user),
            'reading_history': get_user_reading_history(user),
            'preferences': get_user_preferences(user)
        })
        return context


chatbot_view = ChatbotView.as_view()


def chatbot_widget(request):
    """Widget embarcado do chatbot"""
    # Esta view apenas renderiza o template, a lógica é toda via API.
    return render(request, 'chatbot_literario/widget.html')


@csrf_exempt
@require_http_methods(["POST"])
def chatbot_message(request):
    """
    Processa mensagens do chatbot, agora orquestrando a persistência da conversa.
    """
    try:
        data = json.loads(request.body)
        user_message_text = data.get('message', '').strip()
        conversation_id = data.get('conversation_id')
        user = request.user if request.user.is_authenticated else None

        if not user_message_text:
            return JsonResponse({'success': False, 'error': 'Mensagem não pode estar vazia'}, status=400)

        # Lógica de gestão da conversa centralizada aqui.
        conversation = None
        if user and user.is_authenticated and conversation_id:
            try:
                # Carrega a conversa existente
                conversation = Conversation.objects.get(id=conversation_id, user=user)
            except Conversation.DoesNotExist:
                # Se o ID for inválido ou não pertencer ao usuário, cria uma nova.
                conversation = None

        if conversation is None:
            # Cria uma nova conversa se não houver uma ou se a anterior for inválida
            conversation = Conversation.objects.create(
                user=user,
                title=f"Conversa sobre '{user_message_text[:30]}...'"
            )

        # 1. Salva a mensagem do usuário NO CONTEXTO DA CONVERSA CORRETA
        Message.objects.create(
            conversation=conversation,
            content=user_message_text,
            role='user'  #
        )

        # 2. Chama o chatbot, passando a mensagem E o objeto da conversa persistida.
        response_data = functional_chatbot.get_response(
            user_message=user_message_text,
            conversation=conversation  # Passando o objeto inteiro
        )
        bot_response_text = response_data.get('response', 'Desculpe, não consegui processar sua pergunta.')

        # 3. Salva a resposta do bot
        bot_msg_obj = Message.objects.create(
            conversation=conversation,
            content=bot_response_text,
            role='assistant'
        )

        # Atualiza o timestamp da conversa para ordenação
        conversation.save()

        return JsonResponse({
            'success': True,
            'response': bot_response_text,
            'conversation_id': str(conversation.id),  # Retorna o ID da conversa (nova ou existente)
            'message_id': str(bot_msg_obj.id),
            'sources': response_data.get('sources', []),
            'metadata': response_data.get('metadata', {})
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Dados JSON inválidos'}, status=400)
    except Exception as e:
        logger.error(f"Erro ao processar mensagem do chatbot: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': 'Erro interno do servidor'}, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def chatbot_feedback(request):
    """Coleta feedback sobre as respostas do chatbot"""
    try:
        data = json.loads(request.body)
        message_id = data.get('message_id')
        rating = data.get('rating')
        comment = data.get('comment', '')

        if not all([message_id, rating]):
            return JsonResponse({'success': False, 'error': 'message_id e rating são obrigatórios'}, status=400)

        # ✅ CORREÇÃO: Salva o feedback diretamente no banco de dados.
        message_obj = get_object_or_404(Message, id=message_id)

        feedback, created = ConversationFeedback.objects.update_or_create(
            message=message_obj,
            user=request.user,
            defaults={
                'conversation': message_obj.conversation,
                'rating': rating,
                'comment': comment
            }
        )

        return JsonResponse({'success': True, 'message': 'Feedback enviado com sucesso'})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Dados JSON inválidos'}, status=400)
    except Exception as e:
        logger.error(f"Erro ao processar feedback: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': 'Erro interno do servidor'}, status=500)


@login_required
def conversation_history(request):
    """Retorna histórico de conversas do usuário (lista de conversas)"""
    try:
        # ✅ CORREÇÃO: Busca as conversas do usuário logado diretamente do DB.
        conversations = Conversation.objects.filter(user=request.user).order_by('-updated_at')

        data = [
            {
                'id': str(conv.id),
                'title': conv.title or f"Conversa de {conv.started_at.strftime('%d/%m/%Y')}",
                'started_at': conv.started_at.isoformat(),
                'updated_at': conv.updated_at.isoformat(),
            }
            for conv in conversations
        ]

        return JsonResponse({'success': True, 'conversations': data})
    except Exception as e:
        logger.error(f"Erro ao obter histórico de conversas: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': 'Erro ao carregar histórico'}, status=500)


@login_required
def conversation_detail(request, conversation_id):
    """Retorna detalhes (mensagens) de uma conversa específica"""
    try:
        conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
        messages = Message.objects.filter(conversation=conversation).order_by('created_at')

        data = {
            'id': str(conversation.id),
            'title': conversation.title,
            'messages': [
                {
                    'id': str(msg.id),
                    'content': msg.content,
                    'sender': msg.sender,
                    'is_user_message': msg.sender == 'user',
                    'created_at': msg.created_at.isoformat(),
                }
                for msg in messages
            ]
        }
        return JsonResponse({'success': True, 'conversation': data})
    except Exception as e:
        logger.error(f"Erro ao obter detalhes da conversa: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': 'Erro ao carregar conversa'}, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def clear_conversation_context(request):
    """Limpa o contexto da conversa atual no serviço de chatbot."""
    try:
        # ✅ CORREÇÃO: Limpa a sessão no serviço em memória.
        # Uma nova conversa será criada no DB na próxima mensagem.
        functional_chatbot.clear_session(user_id=str(request.user.id))

        logger.info(f"Contexto em memória limpo para usuário {request.user.id}")

        return JsonResponse({'success': True, 'message': 'Contexto limpo. Uma nova conversa será iniciada.'})

    except Exception as e:
        logger.error(f"Erro ao limpar contexto: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': 'Erro interno do servidor'}, status=500)
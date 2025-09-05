# cgbookstore/apps/chatbot_literario/admin_views.py
from django.db import models
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from cgbookstore.apps.chatbot_literario.models import (
    Conversation, Message, KnowledgeItem, TrainingSession, ConversationFeedback
)
# ✅ CORREÇÃO: Importar do PACOTE `services`, não do módulo.
# Isso força a execução do `__init__.py` do pacote.
from cgbookstore.apps.chatbot_literario.services import functional_chatbot, training_service

logger = logging.getLogger(__name__)


# =============================================================================
# FUNÇÕES PRINCIPAIS ESPERADAS PELO SITE.PY
# =============================================================================

@staff_member_required
def training_interface(request):
    """
    Interface principal de treinamento - Página principal do admin do chatbot.
    Esta é a função chamada por /admin/chatbot/treinamento/
    """
    try:
        # Obter estatísticas da base de conhecimento
        knowledge_stats = training_service.get_knowledge_stats()

        # Estatísticas de treinamento recente
        week_ago = timezone.now() - timedelta(days=7)
        recent_training = TrainingSession.objects.filter(
            created_at__gte=week_ago
        ).count()

        # Total de conversas e mensagens
        total_conversations = Conversation.objects.count()
        total_messages = Message.objects.count()

        # ✅ CORREÇÃO: Usar ConversationFeedback ao invés de ChatAnalytics
        total_analytics = ConversationFeedback.objects.count()

        # Conversas recentes para a aba de conversas
        recent_conversations = Conversation.objects.select_related('user').order_by('-started_at')[:10]

        # Preparar dados de estatísticas no formato esperado pelo template
        stats = {
            'total_knowledge': knowledge_stats.get('active_items', 0),
            'active_knowledge': knowledge_stats.get('active_items', 0),
            'total_conversations': total_messages,  # Template espera mensagens aqui
            'total_feedback': total_analytics,
            'recent_knowledge': knowledge_stats.get('recent_additions', 0),
            'satisfaction_rate': 85.0,  # Valor padrão, pode calcular real depois
            'with_embeddings': knowledge_stats.get('with_embeddings', 0),
            'without_embeddings': knowledge_stats.get('without_embeddings', 0),
            'embeddings_available': knowledge_stats.get('embedding_enabled', False),
            'categories': [
                {'category': cat, 'count': count}
                for cat, count in knowledge_stats.get('categories', {}).items()
            ]
        }

        # Template context completo para o template training.html
        context = {
            'title': 'Sistema de Treinamento do Chatbot Literário',
            'stats': stats,
            'knowledge_stats': knowledge_stats,
            'recent_conversations': recent_conversations,
            'system_stats': {
                'total_conversations': total_conversations,
                'total_messages': total_messages,
                'total_analytics': total_analytics,
                'recent_training': recent_training,
            },
        }

        # ✅ CORREÇÃO: Usar o caminho correto do template
        return render(request, 'chatbot_literario/training/training.html', context)

    except Exception as e:
        logger.error(f"Erro na interface de treinamento: {e}")
        messages.error(request, f'Erro ao carregar interface de treinamento: {str(e)}')
        return redirect('admin:index')


@staff_member_required
def test_chatbot(request):
    """
    Página de teste do chatbot - Simulador interativo.
    Esta é a função chamada por /admin/chatbot/treinamento/testar/
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()
            # ✅ CORREÇÃO: Recebe o conversation_id do frontend do simulador
            conversation_id = data.get('conversation_id')

            if not user_message:
                return JsonResponse({'success': False, 'error': 'Mensagem não pode estar vazia'}, status=400)

            # ✅ CORREÇÃO: Lógica para obter ou criar uma conversa de treinamento
            conversation = None
            if conversation_id:
                try:
                    conversation = Conversation.objects.get(id=conversation_id, user=request.user,
                                                            is_training_session=True)
                except Conversation.DoesNotExist:
                    conversation = None  # ID inválido, cria uma nova

            if conversation is None:
                conversation = Conversation.objects.create(
                    user=request.user,
                    is_training_session=True,
                    title=f"Simulador Admin: {timezone.now().strftime('%Y-%m-%d %H:%M')}"
                )

            # Salva a mensagem do admin no histórico da conversa
            Message.objects.create(conversation=conversation, content=user_message, sender='user')

            # ✅ CORREÇÃO: Chama o chatbot com o objeto `conversation`
            response_data = functional_chatbot.get_response(
                user_message=user_message,
                conversation=conversation
            )

            bot_response_text = response_data.get('response', 'Erro ao processar mensagem.')

            # Salva a resposta do bot no histórico
            bot_msg = Message.objects.create(conversation=conversation, content=bot_response_text, sender='bot')

            return JsonResponse({
                'success': True,
                'response': bot_response_text,
                'conversation_id': str(conversation.id),  # Envia o ID de volta para o frontend
                'message_id': str(bot_msg.id),
                'source': response_data.get('source', 'functional_chatbot'),
                'ai_used': response_data.get('model_used') != 'local_knowledge',
            })

        except Exception as e:
            logger.error(f"Erro no teste do chatbot: {e}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    # Redireciona para a interface de treinamento
    return redirect('chatbot_training_dashboard')


@staff_member_required
def add_knowledge_item(request):
    """
    Adiciona item de conhecimento - Interface e processamento.
    Esta é a função chamada por /admin/chatbot/treinamento/adicionar-conhecimento/
    """
    if request.method == 'POST':
        try:
            # Processar dados do formulário
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST

            question = data.get('question', '').strip()
            answer = data.get('answer', '').strip()
            category = data.get('category', 'manual').strip()

            if not question or not answer:
                if request.content_type == 'application/json':
                    return JsonResponse({
                        'success': False,
                        'error': 'Pergunta e resposta são obrigatórias'
                    })
                else:
                    messages.error(request, 'Pergunta e resposta são obrigatórias')
                    return redirect('chatbot_training_dashboard')

            # Adicionar conhecimento usando training_service
            result = training_service.add_knowledge(
                question=question,
                answer=answer,
                category=category
            )

            if result['success']:
                # Registrar sessão de treinamento
                TrainingSession.objects.create(
                    trainer_user=request.user,
                    original_question=question,
                    original_answer='',
                    corrected_answer=answer,
                    knowledge_item_id=result.get('id'),
                    training_type='manual_addition',
                    notes='Adição manual via interface admin'
                )

                if request.content_type == 'application/json':
                    return JsonResponse(result)
                else:
                    messages.success(request, 'Conhecimento adicionado com sucesso!')
                    return redirect('chatbot_training_dashboard')
            else:
                if request.content_type == 'application/json':
                    return JsonResponse(result)
                else:
                    messages.error(request, result['message'])
                    return redirect('chatbot_training_dashboard')

        except Exception as e:
            logger.error(f"Erro ao adicionar conhecimento: {e}")
            if request.content_type == 'application/json':
                return JsonResponse({
                    'success': False,
                    'error': f'Erro interno: {str(e)}'
                })
            else:
                messages.error(request, f'Erro interno: {str(e)}')
                return redirect('chatbot_training_dashboard')

    # GET - Redirecionar para a interface de treinamento
    return redirect('chatbot_training_dashboard')


@csrf_exempt
@staff_member_required
@require_http_methods(["POST"])
def add_to_knowledge(request):
    """
    Adiciona conhecimento de conversa existente.
    Esta é a função chamada por /admin/chatbot/treinamento/adicionar-da-conversa/
    """
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        conversation_id = data.get('conversation_id')
        message_id = data.get('message_id')
        user_input = data.get('user_input', '').strip()
        bot_response = data.get('bot_response', '').strip()

        if not all([user_input, bot_response]):
            return JsonResponse({
                'success': False,
                'error': 'Pergunta e resposta são obrigatórias'
            })

        # Usar training_service para adicionar
        result = training_service.add_knowledge(
            question=user_input,
            answer=bot_response,
            category='from_conversation'
        )

        if result['success']:
            # Registrar sessão de treinamento
            TrainingSession.objects.create(
                trainer_user=request.user,
                original_question=user_input,
                original_answer='',
                corrected_answer=bot_response,
                knowledge_item_id=result.get('id'),
                training_type='manual_addition',
                notes=f'Adição de conversa ID: {conversation_id}, Mensagem ID: {message_id}'
            )

            messages.success(request, 'Conhecimento adicionado com sucesso!')
        else:
            messages.error(request, result['message'])

        return redirect('chatbot_training_dashboard')

    except Exception as e:
        logger.error(f"Erro em add_to_knowledge: {e}")
        messages.error(request, f'Erro interno: {str(e)}')
        return redirect('chatbot_training_dashboard')


@staff_member_required
def import_knowledge(request):
    """
    Importa conhecimento de arquivo.
    Esta é a função chamada por /admin/chatbot/treinamento/importar/
    """
    if request.method == 'POST':
        try:
            if 'import_file' not in request.FILES:
                messages.error(request, 'Nenhum arquivo foi enviado')
                return redirect('chatbot_training_dashboard')

            uploaded_file = request.FILES['import_file']

            if not uploaded_file.name.endswith('.json'):
                messages.error(request, 'Apenas arquivos JSON são suportados')
                return redirect('chatbot_training_dashboard')

            # Ler e processar arquivo JSON
            file_content = uploaded_file.read().decode('utf-8')
            knowledge_data = json.loads(file_content)

            imported_count = 0
            error_count = 0

            # Determinar estrutura do arquivo
            if isinstance(knowledge_data, dict) and 'knowledge_base' in knowledge_data:
                items = knowledge_data['knowledge_base']
            elif isinstance(knowledge_data, list):
                items = knowledge_data
            else:
                messages.error(request, 'Formato de arquivo inválido')
                return redirect('chatbot_training_dashboard')

            # Processar cada item
            for item in items:
                try:
                    question = item.get('question', '').strip()
                    answer = item.get('answer', '').strip()
                    category = item.get('category', 'imported')

                    if question and answer:
                        result = training_service.add_knowledge(
                            question=question,
                            answer=answer,
                            category=category
                        )

                        if result['success']:
                            imported_count += 1

                            # Registrar sessão de treinamento
                            TrainingSession.objects.create(
                                trainer_user=request.user,
                                original_question=question,
                                original_answer='',
                                corrected_answer=answer,
                                knowledge_item_id=result.get('id'),
                                training_type='bulk_training',
                                notes=f'Importação de arquivo: {uploaded_file.name}'
                            )
                        else:
                            error_count += 1
                    else:
                        error_count += 1

                except Exception as e:
                    logger.error(f"Erro ao processar item: {e}")
                    error_count += 1

            # Mensagens de resultado
            if imported_count > 0:
                messages.success(request, f'{imported_count} itens importados com sucesso')
            if error_count > 0:
                messages.warning(request, f'{error_count} itens não puderam ser importados')

        except Exception as e:
            logger.error(f"Erro na importação: {e}")
            messages.error(request, f'Erro na importação: {str(e)}')

        return redirect('chatbot_training_dashboard')

    # GET - Redirecionar para a interface de treinamento
    return redirect('chatbot_training_dashboard')


@staff_member_required
def export_knowledge(request):
    """
    Exporta base de conhecimento.
    Esta é a função chamada por /admin/chatbot/treinamento/exportar/
    """
    try:
        format_type = request.POST.get('format', 'json')
        active_only = request.POST.get('active_only', 'true').lower() == 'true'

        # Usar training_service para exportar
        export_result = training_service.export_knowledge_data(
            format_type=format_type,
            active_only=active_only
        )

        if export_result['success']:
            if format_type == 'json':
                response = HttpResponse(
                    json.dumps(export_result, indent=2, ensure_ascii=False),
                    content_type='application/json'
                )
                filename = f"knowledge_base_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
        else:
            messages.error(request, export_result['message'])

    except Exception as e:
        logger.error(f"Erro na exportação: {e}")
        messages.error(request, f'Erro na exportação: {str(e)}')

    return redirect('chatbot_training_dashboard')


@staff_member_required
def update_embeddings(request):
    """
    Atualiza embeddings da base de conhecimento a partir de um formulário do admin.
    """
    # ✅ Garante que a view só responde a requisições POST
    if request.method != 'POST':
        messages.error(request, "Ação inválida. Use o botão no painel.")
        return redirect('chatbot_training_dashboard')

    try:
        # Usar training_service para atualizar embeddings
        result = training_service.update_all_embeddings()

        if result.get('success'):
            # ✅ Adiciona uma mensagem de sucesso para o usuário
            messages.success(
                request,
                f"Atualização de embeddings concluída! {result.get('updated_count', 0)} itens processados."
            )

            # Registrar sessão de treinamento
            TrainingSession.objects.create(
                trainer_user=request.user,
                training_type='embedding_update',
                notes=f"Atualização de embeddings: {result.get('updated_count', 0)} itens processados, {result.get('error_count', 0)} erros."
            )
        else:
            # ✅ Adiciona uma mensagem de erro
            error_msg = result.get('message', 'Ocorreu um erro desconhecido.')
            messages.error(request, f"Falha ao atualizar embeddings: {error_msg}")

    except Exception as e:
        logger.error(f"Erro na atualização de embeddings: {e}", exc_info=True)
        # ✅ Adiciona uma mensagem de erro genérica
        messages.error(request, f'Erro interno do servidor ao atualizar embeddings: {str(e)}')

    # ✅ Redireciona o usuário de volta para o painel principal
    return redirect('chatbot_training_dashboard')


# =============================================================================
# FUNÇÕES ADICIONAIS ESPERADAS PELO SITE.PY
# =============================================================================

@staff_member_required
def run_add_specific_dates(request):
    """
    Adiciona datas específicas à base de conhecimento.
    """
    try:
        specific_dates = [
            ("Em que ano O Hobbit foi publicado?", "O Hobbit foi publicado em 1937."),
            ("Quando O Senhor dos Anéis foi publicado?", "O Senhor dos Anéis foi publicado entre 1954 e 1955."),
            ("Em que ano Dom Casmurro foi publicado?", "Dom Casmurro foi publicado em 1899."),
            ("Quando Harry Potter e a Pedra Filosofal foi lançado?",
             "Harry Potter e a Pedra Filosofal foi publicado em 1997."),
            ("Em que ano Cem Anos de Solidão foi publicado?", "Cem Anos de Solidão foi publicado em 1967."),
            ("Quando 1984 de George Orwell foi publicado?", "1984 foi publicado em 1949."),
        ]

        added_count = 0
        for question, answer in specific_dates:
            result = training_service.add_knowledge(
                question=question,
                answer=answer,
                category='specific_dates'
            )
            if result['success']:
                added_count += 1

        messages.success(request, f'{added_count} datas específicas adicionadas à base de conhecimento')

    except Exception as e:
        logger.error(f"Erro ao adicionar datas específicas: {e}")
        messages.error(request, f'Erro: {str(e)}')

    return redirect('chatbot_training_dashboard')


@staff_member_required
def run_debug_chatbot(request):
    """Debug do sistema de chatbot."""
    try:
        knowledge_stats = training_service.get_knowledge_stats()
        quality_metrics = training_service.get_quality_metrics()
        debug_info = functional_chatbot.get_statistics()

        context = {
            'title': 'Resultados do Debug do Chatbot',
            'knowledge_stats': knowledge_stats,
            'quality_metrics': quality_metrics,
            'debug_info': debug_info,
            'recent_training': None,  # Não aplicável para esta view
        }
        # ✅ Renderiza a nova dashboard
        return render(request, 'admin/chatbot_literario/debug_results.html', context)

    except Exception as e:
        logger.error(f"Erro no debug: {e}", exc_info=True)
        messages.error(request, f'Erro no debug: {str(e)}')
        return redirect('chatbot_training_dashboard')


@staff_member_required
def system_statistics(request):
    """Estatísticas do sistema."""
    try:
        stats = training_service.get_knowledge_stats()
        quality_metrics = training_service.get_quality_metrics()

        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_training = TrainingSession.objects.filter(
            created_at__gte=thirty_days_ago
        ).values('training_type').annotate(
            count=Count('id')
        ).order_by('-count')

        context = {
            'title': 'Estatísticas do Sistema',
            'knowledge_stats': stats,
            'quality_metrics': quality_metrics,
            'recent_training': recent_training,
            'debug_info': None,  # Não aplicável para esta view
        }
        # ✅ Renderiza a nova dashboard
        return render(request, 'admin/chatbot_literario/debug_results.html', context)

    except Exception as e:
        logger.error(f"Erro nas estatísticas: {e}", exc_info=True)
        messages.error(request, f'Erro: {str(e)}')
        return redirect('chatbot_training_dashboard')


@staff_member_required
def clean_knowledge_base(request):
    """
    Limpeza da base de conhecimento.
    """
    if request.method == 'POST':
        try:
            result = training_service.clean_knowledge_base()

            if result['success']:
                # Registrar sessão de treinamento
                TrainingSession.objects.create(
                    trainer_user=request.user,
                    original_question='',
                    original_answer='',
                    corrected_answer='',
                    training_type='knowledge_cleanup',
                    notes=f'Limpeza da KB: {result.get("stats", {})}'
                )

                messages.success(request, result['message'])
            else:
                messages.error(request, result['message'])

        except Exception as e:
            logger.error(f"Erro na limpeza: {e}")
            messages.error(request, f'Erro na limpeza: {str(e)}')

    return redirect('chatbot_training_dashboard')


@staff_member_required
def system_config(request):
    """
    Configuração do sistema.
    """
    try:
        context = {
            'title': 'Configuração do Sistema',
            'config_info': {
                'embedding_enabled': training_service.initialized,
                'knowledge_stats': training_service.get_knowledge_stats(),
            }
        }
        return render(request, 'admin/chatbot_literario/system_config.html', context)

    except Exception as e:
        logger.error(f"Erro na configuração: {e}")
        messages.error(request, f'Erro: {str(e)}')
        return redirect('chatbot_training_dashboard')


# =============================================================================
# FUNÇÕES DE COMPATIBILIDADE E REDIRECIONAMENTO
# =============================================================================

@staff_member_required
def admin_dashboard(request):
    """
    Dashboard principal - redireciona para training_interface.
    """
    return training_interface(request)


@staff_member_required
def chatbot_simulator(request):
    """
    Simulador do chatbot - redireciona para test_chatbot.
    """
    return test_chatbot(request)
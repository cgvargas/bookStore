import json
import csv
import io
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import path
from django.contrib import messages
from django.utils.html import escape

from .models import Conversation, Message, KnowledgeItem, ConversationFeedback
from .services.chatbot_service import chatbot
from .services.training_service import training_service


@staff_member_required
def training_interface(request):
    """Renderiza a interface de treinamento do chatbot."""
    # Inicializar serviço de treinamento se necessário
    if not training_service.initialized:
        training_service.initialize()

    # Obter estatísticas
    stats = training_service.generate_training_statistics()

    # Obter conversas recentes
    recent_conversations = training_service.get_conversations_with_metadata(limit=20)

    context = {
        'title': 'Treinamento do Chatbot Literário',
        'stats': stats,
        'recent_conversations': recent_conversations
    }

    # Mudar para usar o novo template
    return render(request, 'chatbot_literario/training/training.html', context)


@staff_member_required
@csrf_exempt
def test_chatbot(request):
    """Endpoint para testar o chatbot na interface de administração."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()

        if not message:
            return JsonResponse({'error': 'Mensagem vazia'}, status=400)

        # Obter resposta do chatbot
        response, _ = chatbot.get_response(message, user=request.user)

        # Não é mais necessário adicionar à conversation_data, pois agora
        # usamos o banco de dados para armazenar conversas

        return JsonResponse({
            'response': response
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
def add_knowledge_item(request):
    """Adiciona um item à base de conhecimento."""
    if request.method != 'POST':
        return redirect('admin:chatbot_literario_training')

    question = request.POST.get('question', '').strip()
    answer = request.POST.get('answer', '').strip()
    category = request.POST.get('category', '').strip()
    source = request.POST.get('source', 'manual').strip()

    if not question or not answer:
        messages.error(request, 'Pergunta e resposta são obrigatórias')
        return redirect('admin:chatbot_literario_training')

    # Inicializar serviço de treinamento se necessário
    if not training_service.initialized:
        training_service.initialize()

    # Adicionar à base de conhecimento
    success = training_service.add_knowledge_item(question, answer, category=category, source=source)

    if success:
        messages.success(request, 'Item adicionado com sucesso à base de conhecimento')
    else:
        messages.error(request, 'Erro ao adicionar item à base de conhecimento')

    return redirect('admin:chatbot_literario_training')


@staff_member_required
def add_to_knowledge(request):
    """Adiciona uma conversa existente à base de conhecimento."""
    if request.method != 'POST':
        return redirect('admin:chatbot_literario_training')

    user_input = request.POST.get('user_input', '').strip()
    bot_response = request.POST.get('bot_response', '').strip()

    if not user_input or not bot_response:
        messages.error(request, 'Mensagem do usuário e resposta do bot são obrigatórias')
        return redirect('admin:chatbot_literario_training')

    # Inicializar serviço de treinamento se necessário
    if not training_service.initialized:
        training_service.initialize()

    # Adicionar à base de conhecimento
    success = training_service.add_knowledge_item(
        user_input,
        bot_response,
        category='conversas',
        source='conversa'
    )

    if success:
        messages.success(request, 'Conversa adicionada com sucesso à base de conhecimento')
    else:
        messages.error(request, 'Erro ao adicionar conversa à base de conhecimento')

    return redirect('admin:chatbot_literario_training')


@staff_member_required
def import_knowledge(request):
    """Importa base de conhecimento de um arquivo."""
    if request.method != 'POST':
        return redirect('admin:chatbot_literario_training')

    import_file = request.FILES.get('import_file')
    format_type = request.POST.get('format', 'csv')

    if not import_file:
        messages.error(request, 'Arquivo não fornecido')
        return redirect('admin:chatbot_literario_training')

    # Inicializar serviço de treinamento se necessário
    if not training_service.initialized:
        training_service.initialize()

    try:
        count = 0

        if format_type == 'csv':
            # Processar CSV
            decoded_file = import_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)

            for row in reader:
                if 'question' in row and 'answer' in row:
                    category = row.get('category', 'importado')
                    source = row.get('source', 'importacao')

                    success = training_service.add_knowledge_item(
                        row['question'],
                        row['answer'],
                        category=category,
                        source=source
                    )
                    if success:
                        count += 1

        elif format_type == 'json':
            # Processar JSON
            data = json.load(import_file)

            if isinstance(data, list):
                for item in data:
                    if 'question' in item and 'answer' in item:
                        category = item.get('category', 'importado')
                        source = item.get('source', 'importacao')

                        success = training_service.add_knowledge_item(
                            item['question'],
                            item['answer'],
                            category=category,
                            source=source
                        )
                        if success:
                            count += 1
            else:
                messages.error(request, 'Formato JSON inválido. Deve ser uma lista de objetos.')
                return redirect('admin:chatbot_literario_training')

        else:
            messages.error(request, f'Formato não suportado: {format_type}')
            return redirect('admin:chatbot_literario_training')

        messages.success(request, f'{count} itens importados com sucesso')
    except Exception as e:
        messages.error(request, f'Erro ao importar arquivo: {str(e)}')

    return redirect('admin:chatbot_literario_training')


@staff_member_required
def export_knowledge(request):
    """Exporta base de conhecimento para um arquivo."""
    if request.method != 'POST':
        return redirect('admin:chatbot_literario_training')

    format_type = request.POST.get('format', 'csv')

    # Inicializar serviço de treinamento se necessário
    if not training_service.initialized:
        training_service.initialize()

    try:
        # Obter itens da base de conhecimento
        knowledge_items = KnowledgeItem.objects.all()

        if format_type == 'csv':
            # Exportar para CSV
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="knowledge_base.csv"'

            writer = csv.writer(response)
            writer.writerow(['question', 'answer', 'category', 'source', 'active'])

            for item in knowledge_items:
                writer.writerow([
                    item.question,
                    item.answer,
                    item.category,
                    item.source,
                    item.active
                ])

            return response

        elif format_type == 'json':
            # Exportar para JSON
            response = HttpResponse(content_type='application/json')
            response['Content-Disposition'] = 'attachment; filename="knowledge_base.json"'

            # Filtrar para remover campos como embeddings que não são serializáveis
            filtered_data = []
            for item in knowledge_items:
                filtered_item = {
                    'question': item.question,
                    'answer': item.answer,
                    'category': item.category,
                    'source': item.source,
                    'active': item.active,
                    'created_at': item.created_at.isoformat(),
                    'updated_at': item.updated_at.isoformat()
                }
                filtered_data.append(filtered_item)

            json.dump(filtered_data, response, ensure_ascii=False, indent=2)

            return response

        else:
            messages.error(request, f'Formato não suportado: {format_type}')
            return redirect('admin:chatbot_literario_training')

    except Exception as e:
        messages.error(request, f'Erro ao exportar: {str(e)}')
        return redirect('admin:chatbot_literario_training')


@staff_member_required
def update_embeddings(request):
    """Atualiza embeddings para itens da base de conhecimento."""
    if request.method != 'POST':
        return redirect('admin:chatbot_literario_training')

    # Inicializar serviço de treinamento se necessário
    if not training_service.initialized:
        training_service.initialize()

    batch_size = int(request.POST.get('batch_size', 100))

    try:
        updated = training_service.update_embeddings(batch_size=batch_size)

        if updated > 0:
            messages.success(request, f'Embeddings atualizados para {updated} itens.')
        else:
            messages.info(request, 'Nenhum item para atualizar ou modelo não disponível.')

    except Exception as e:
        messages.error(request, f'Erro ao atualizar embeddings: {str(e)}')

    return redirect('admin:chatbot_literario_training')


# Novas visualizações para gerenciar conversas e feedback
@staff_member_required
def conversation_list(request):
    """Lista todas as conversações do chatbot."""
    conversations = Conversation.objects.all().order_by('-updated_at')[:50]

    context = {
        'title': 'Conversas do Chatbot Literário',
        'conversations': conversations
    }

    return render(request, 'chatbot_literario/conversation_list.html', context)


@staff_member_required
def feedback_list(request):
    """Lista todos os feedbacks do chatbot."""
    feedbacks = ConversationFeedback.objects.all().order_by('-timestamp')[:50]

    context = {
        'title': 'Feedbacks do Chatbot Literário',
        'feedbacks': feedbacks
    }

    return render(request, 'chatbot_literario/feedback_list.html', context)


# URLs para admin
def get_admin_urls():
    """Retorna URLs para integração com admin."""
    return [
        path('treinamento/', training_interface, name='chatbot_literario_training'),
        path('treinamento/testar/', test_chatbot, name='test_chatbot'),
        path('treinamento/adicionar-conhecimento/', add_knowledge_item, name='add_knowledge_item'),
        path('treinamento/adicionar-da-conversa/', add_to_knowledge, name='add_to_knowledge'),
        path('treinamento/importar/', import_knowledge, name='import_knowledge'),
        path('treinamento/exportar/', export_knowledge, name='export_knowledge'),
        path('treinamento/update-embeddings/', update_embeddings, name='update_embeddings'),
        # Adicionando novas URLs para conversas e feedbacks com caminhos absolutos
        path('conversation/', conversation_list, name='conversation_list'),
        path('conversationfeedback/', feedback_list, name='feedback_list'),
    ]
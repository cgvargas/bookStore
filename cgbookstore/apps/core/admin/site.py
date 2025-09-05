# Arquivo: cgbookstore/apps/core/admin/site.py

import os
import json
import logging
from django.contrib import admin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.urls import path
from django.core import management
from django.contrib import messages
from django.conf import settings

# Importações de modelos necessários
from ..models.home_content import HomeSection, HomeSectionBookItem
from ..models.book import Book

# Importações para as views personalizadas
from . import views as admin_custom_views
from . import diagnostics_admin  # Importação para as views de diagnóstico
from cgbookstore.apps.chatbot_literario import admin_views as chatbot_views

logger = logging.getLogger(__name__)


class DatabaseAdminSite(admin.AdminSite):
    site_header = 'Administração CG BookStore'
    site_title = 'Portal Administrativo CG BookStore'
    index_title = 'Gerenciamento do Sistema'

    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            # URLs de Gerenciamento Geral
            path('view-database/', self.admin_view(self.view_database), name='view-database'),
            path('generate-schema/', self.admin_view(self.generate_schema_view), name='generate-schema'),
            path('generate-structure/', self.admin_view(self.generate_structure_view), name='generate-structure'),
            path('export-data/json/', self.admin_view(self.export_data_json), name='export-data-json'),
            path('clear-folders/all/', self.admin_view(self.clear_folders_view), name='clear-folders'),
            path('book-category-config/', self.admin_view(self.book_category_config_view), name='book-category-config'),
            path('visual-shelf-manager/', self.admin_view(self.visual_shelf_manager), name='visual-shelf-manager'),

            # URLs do Chatbot
            path('chatbot/treinamento/', self.admin_view(chatbot_views.training_interface),
                 name='chatbot_literario_training'),
            path('chatbot/conversas/', self.admin_view(self.chatbot_conversations_view), name='chatbot_conversations'),
            path('chatbot/feedbacks/', self.admin_view(self.chatbot_feedbacks_view), name='chatbot_feedbacks'),

            # ==============================================================================
            # URLs DE DIAGNÓSTICO REINTEGRADAS
            # ==============================================================================
            path('diagnostics/', self.admin_view(diagnostics_admin.diagnostics_dashboard),
                 name='diagnostics_dashboard'),
            path('diagnostics/performance/', self.admin_view(diagnostics_admin.performance_diagnostics),
                 name='performance_diagnostics'),
            path('diagnostics/redis-info/', self.admin_view(diagnostics_admin.redis_info), name='redis_info'),
            path('diagnostics/fix-covers/', self.admin_view(diagnostics_admin.fix_corrupted_covers),
                 name='fix_corrupted_covers'),
            path('diagnostics/debug-books/', self.admin_view(diagnostics_admin.debug_book_images),
                 name='debug_book_images'),
            path('diagnostics/debug-recommendations/', self.admin_view(diagnostics_admin.debug_recommendations),
                 name='debug_recommendations'),
            path('diagnostics/system-health/', self.admin_view(diagnostics_admin.system_health_check),
                 name='system_health_check'),
            path('diagnostics/clear-cache/', self.admin_view(diagnostics_admin.clear_cache), name='clear_cache'),
            path('diagnostics/task-status/<str:task_id>/', self.admin_view(diagnostics_admin.task_status),
                 name='task_status'),
        ]

        return custom_urls + urls

    def generate_schema_view(self, request):
        try:
            base_dir = os.path.dirname(settings.BASE_DIR)
            output_dir = os.path.join(base_dir, 'database_schemas')
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            management.call_command('generate_tables', output_dir=output_dir)
            messages.success(request, 'Schema do banco de dados gerado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao gerar schema: {str(e)}')
        return HttpResponse('<script>window.history.back()</script>')

    def generate_structure_view(self, request):
        try:
            base_dir = os.path.dirname(settings.BASE_DIR)
            output_dir = os.path.join(base_dir, 'project_structure')
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            management.call_command('generate_project_structure', output_dir=output_dir)
            messages.success(request, 'Estrutura do projeto gerada com sucesso.')
        except Exception as e:
            messages.error(request, f'Erro ao gerar estrutura: {str(e)}')
        return HttpResponse('<script>window.history.back()</script>')

    def export_data_json(self, request):
        data = {}
        try:
            for model, model_admin in self._registry.items():
                model_name = model.__name__
                data[model_name] = list(model.objects.all().values())
            response_data = json.dumps(data, indent=4, ensure_ascii=False, default=str)
            response = HttpResponse(response_data, content_type='application/json')
            response['Content-Disposition'] = 'attachment; filename="database_dump.json"'
            messages.success(request, "Dados exportados com sucesso para JSON!")
            return response
        except Exception as e:
            messages.error(request, f"Erro ao exportar dados: {str(e)}")
            return redirect('admin:index')

    def clear_folders_view(self, request):
        messages.info(request, "Funcionalidade de limpar pastas em refatoração.")
        return redirect('admin:index')

    def view_database(self, request):
        try:
            tables = {model._meta.model_name: model for model in self._registry}
            table_name = request.GET.get('table')
            if table_name and table_name in tables:
                model = tables[table_name]
                objects = model.objects.all().values()
                context = {
                    'table_name': table_name,
                    'data': objects,
                    'columns': [field.name for field in model._meta.fields]
                }
                return render(request, 'admin/database_table_view.html', context)
            context = {'tables': list(tables.keys())}
            return render(request, 'admin/database_overview.html', context)
        except Exception as e:
            messages.error(request, f'Erro ao visualizar banco de dados: {str(e)}')
            return redirect('admin:index')

    def book_category_config_view(self, request):
        messages.info(request, "A configuração de categorias de livros está em refatoração para a nova estrutura.")
        return redirect('admin:index')

    def visual_shelf_manager(self, request):
        if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                data = json.loads(request.body)
                action = data.get('action')
                book_id = data.get('book_id')
                section_id = data.get('section_id')
                if not all([action, book_id, section_id]):
                    return JsonResponse({'status': 'error', 'message': 'Dados incompletos'}, status=400)
                section = HomeSection.objects.get(id=section_id, tipo='shelf')
                if action == 'add':
                    next_order = section.manual_books.count()
                    HomeSectionBookItem.objects.create(section=section, book_id=book_id, ordem=next_order)
                    return JsonResponse({'status': 'success', 'message': 'Livro adicionado.'})
                elif action == 'remove':
                    HomeSectionBookItem.objects.filter(section=section, book_id=book_id).delete()
                    return JsonResponse({'status': 'success', 'message': 'Livro removido.'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

        shelves = HomeSection.objects.filter(tipo='shelf', ativo=True, shelf_behavior='manual').prefetch_related(
            'manual_books')
        used_book_ids = HomeSectionBookItem.objects.values_list('book_id', flat=True)
        unassigned_books = Book.objects.exclude(id__in=used_book_ids)[:100]
        context = {
            'title': 'Gerenciador Visual de Prateleiras',
            'shelves': shelves,
            'unassigned_books': unassigned_books,
        }
        return render(request, 'admin/visual_shelf_manager.html', context)

    def chatbot_conversations_view(self, request):
        from cgbookstore.apps.chatbot_literario.models import Conversation
        context = {
            'title': 'Conversas do Chatbot',
            'conversations': Conversation.objects.all().order_by('-updated_at'),
        }
        return render(request, 'admin/chatbot_literario/conversation_list.html', context)

    def chatbot_feedbacks_view(self, request):
        from cgbookstore.apps.chatbot_literario.models import ConversationFeedback
        context = {
            'title': 'Feedbacks do Chatbot',
            'feedbacks': ConversationFeedback.objects.all().order_by('-timestamp'),
        }
        return render(request, 'admin/chatbot_literario/feedback_list.html', context)

    def index(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}
        chatbot_links = [
            {'name': 'Treinamento do Chatbot', 'url': '/admin/chatbot/treinamento/'},
            {'name': 'Conversas', 'url': '/admin/chatbot/conversas/'},
            {'name': 'Feedbacks', 'url': '/admin/chatbot/feedbacks/'}
        ]
        extra_context['chatbot_links'] = chatbot_links
        return super().index(request, extra_context)
# cgbookstore/apps/core/admin.py

import os
import json
import logging
from datetime import datetime
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import path
from django.core import management
from django.contrib import messages
from django.contrib.auth.models import Group
from django.conf import settings
from .models import User, Profile, Book, UserBookShelf
from .models.banner import Banner

logger = logging.getLogger(__name__)


class DatabaseAdminSite(admin.AdminSite):
    site_header = 'CG BookStore Admin'
    site_title = 'CG BookStore Admin Portal'
    index_title = 'Administração CG BookStore'

    def generate_schema_view(self, request):
        try:
            base_dir = os.path.dirname(settings.BASE_DIR)
            output_dir = os.path.join(base_dir, 'database_schemas')

            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            current_date = datetime.now().strftime('%Y%m%d_%H%M%S')
            management.call_command('generate_tables', output_dir=output_dir)

            messages.success(request, 'Schema do banco de dados gerado com sucesso!')
            logger.info(f'Schema gerado com sucesso em: {output_dir}')
        except Exception as e:
            logger.error(f'Erro ao gerar schema: {str(e)}')
            messages.error(request, f'Erro ao gerar schema: {str(e)}')

        return HttpResponse('<script>window.history.back()</script>')

    def generate_structure_view(self, request):
        try:
            base_dir = os.path.dirname(settings.BASE_DIR)
            output_dir = os.path.join(base_dir, 'project_structure')

            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            current_date = datetime.now().strftime('%Y%m%d_%H%M%S')
            csv_filename = f'project_structure_{current_date}.csv'
            csv_path = os.path.join(output_dir, csv_filename)

            management.call_command('generate_project_structure', output_dir=output_dir)

            if os.path.exists(csv_path):
                messages.success(
                    request,
                    f'Estrutura do projeto gerada com sucesso em: {csv_path}'
                )
            else:
                messages.warning(
                    request,
                    f'Arquivo gerado mas não encontrado no caminho esperado: {csv_path}'
                )

            logger.info(f'Tentando gerar estrutura em: {output_dir}')
            logger.info(f'Arquivo CSV esperado em: {csv_path}')
        except Exception as e:
            logger.error(f'Erro ao gerar estrutura: {str(e)}')
            messages.error(
                request,
                f'Erro ao gerar estrutura do projeto: {str(e)}'
            )
        return HttpResponse('<script>window.history.back()</script>')

    def export_data_json(self, request):
        """
        Exporta todos os dados do banco de dados em formato JSON.
        """
        data = {}
        try:
            for model, model_admin in self._registry.items():
                model_name = model.__name__
                data[model_name] = list(model.objects.all().values())

            response = HttpResponse(content_type='application/json')
            response['Content-Disposition'] = 'attachment; filename="database_dump.json"'
            response.write(json.dumps(data, indent=4, ensure_ascii=False))

            messages.success(request, "Dados exportados com sucesso para JSON!")
            return response
        except Exception as e:
            logger.error(f"Erro ao exportar dados: {str(e)}")
            messages.error(request, f"Erro ao exportar dados: {str(e)}")
            return HttpResponse('<script>window.history.back()</script>')

    def _clear_folder_content(self, folder_path, folder_name):
        folder_status = {'files_removed': 0, 'errors': []}

        if not os.path.exists(folder_path):
            logger.warning(f'Pasta {folder_name} não encontrada em: {folder_path}')
            return folder_status

        def remove_recursive(path):
            try:
                for root, dirs, files in os.walk(path, topdown=False):
                    for file in files:
                        try:
                            file_path = os.path.join(root, file)
                            os.chmod(file_path, 0o777)
                            os.unlink(file_path)
                            folder_status['files_removed'] += 1
                            logger.info(f'Arquivo removido: {file_path}')
                        except Exception as e:
                            folder_status['errors'].append(f'Erro ao remover arquivo {file}: {e}')
                            logger.error(f'Erro ao remover arquivo {file}: {e}')

                    for dir_name in dirs:
                        try:
                            os.rmdir(os.path.join(root, dir_name))
                        except Exception as e:
                            folder_status['errors'].append(f'Erro ao remover pasta {dir_name}: {e}')
                            logger.error(f'Erro ao remover pasta {dir_name}: {e}')

            except Exception as e:
                folder_status['errors'].append(f'Erro ao processar {path}: {e}')
                logger.error(f'Erro ao processar {path}: {e}')

        remove_recursive(folder_path)
        return folder_status

    def clear_schema_folder_view(self, request):
        base_dir = os.path.dirname(settings.BASE_DIR)
        schema_dir = os.path.join(base_dir, 'database_schemas')
        status = self._clear_folder_content(schema_dir, 'database_schemas')

        if status['files_removed'] > 0:
            messages.success(request, f"Schema: {status['files_removed']} arquivo(s) removido(s)")
        if status['errors']:
            for error in status['errors']:
                messages.error(request, error)

        return HttpResponse('<script>window.history.back()</script>')

    def clear_structure_folder_view(self, request):
        base_dir = os.path.dirname(settings.BASE_DIR)
        structure_dir = os.path.join(base_dir, 'project_structure')
        status = self._clear_folder_content(structure_dir, 'project_structure')

        if status['files_removed'] > 0:
            messages.success(request, f"Estrutura: {status['files_removed']} arquivo(s) removido(s)")
        if status['errors']:
            for error in status['errors']:
                messages.error(request, error)

        return HttpResponse('<script>window.history.back()</script>')

    def clear_folders_view(self, request):
        base_dir = os.path.dirname(settings.BASE_DIR)
        schema_dir = os.path.join(base_dir, 'database_schemas')
        structure_dir = os.path.join(base_dir, 'project_structure')

        schema_status = self._clear_folder_content(schema_dir, 'database_schemas')
        structure_status = self._clear_folder_content(structure_dir, 'project_structure')

        for name, status in [('Schema', schema_status), ('Estrutura', structure_status)]:
            if status['files_removed'] > 0:
                messages.success(request, f"{name}: {status['files_removed']} arquivo(s) removido(s)")
            if status['errors']:
                for error in status['errors']:
                    messages.error(request, error)

        return HttpResponse('<script>window.history.back()</script>')

    def view_database(self, request):
        """
        Visualiza os dados de todas as tabelas do banco, ou dados filtrados por tabela específica.
        """
        try:
            # Lista todas as tabelas registradas no admin.
            tables = {model._meta.model_name: model for model in self._registry}

            # Caso um filtro por tabela seja solicitado.
            table_name = request.GET.get('table')
            if table_name:
                model = tables.get(table_name)
                if model:
                    objects = model.objects.all().values()
                    context = {
                        'table_name': table_name,
                        'data': objects,  # Dados retornados como lista
                        'columns': [field.name for field in model._meta.fields]
                    }
                    return render(request, 'admin/database_table_view.html', context)

                messages.error(request, f'Tabela "{table_name}" não encontrada.')
                return HttpResponse('<script>window.history.back()</script>')

            # Renderizar a tela inicial com as tabelas registradas.
            context = {'tables': tables.keys()}
            return render(request, 'admin/database_overview.html', context)

        except Exception as e:
            logger.error(f'Erro ao visualizar banco de dados: {str(e)}')
            messages.error(request, f'Erro ao visualizar banco de dados: {str(e)}')
            return HttpResponse('<script>window.history.back()</script>')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('view-database/', self.admin_view(self.view_database), name='view-database'),  # Nova rota
            path('generate-schema/', self.admin_view(self.generate_schema_view), name='generate-schema'),
            path('generate-structure/', self.admin_view(self.generate_structure_view), name='generate-structure'),
            path('export-data/json/', self.admin_view(self.export_data_json), name='export-data-json'),
            path('clear-folders/all/', self.admin_view(self.clear_folders_view), name='clear-folders'),
            path('clear-folders/schema/', self.admin_view(self.clear_schema_folder_view), name='clear-schema-folder'),
            path('clear-folders/structure/', self.admin_view(self.clear_structure_folder_view), name='clear-structure-folder'),
        ]
        return custom_urls + urls


admin_site = DatabaseAdminSite(name='admin')

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'cpf', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'cpf')
    readonly_fields = ('date_joined', 'modified')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informações Pessoais',
         {'fields': ('first_name', 'last_name', 'email', 'cpf', 'data_nascimento', 'telefone', 'foto')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Datas Importantes', {'fields': ('last_login', 'date_joined', 'modified')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'cpf', 'password1', 'password2'),
        }),
    )

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'birth_date', 'updated_at')
    search_fields = ('user__username', 'user__email', 'location')
    list_filter = ('updated_at',)
    raw_id_fields = ('user',)


class BannerAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'ativo', 'ordem', 'data_inicio', 'data_fim')
    list_filter = ('ativo',)
    search_fields = ('titulo', 'subtitulo', 'descricao')
    ordering = ('ordem', '-data_inicio')
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('titulo', 'subtitulo', 'descricao', 'link')
        }),
        ('Imagens', {
            'fields': ('imagem', 'imagem_mobile'),
            'description': 'Upload das imagens do banner. Recomendado: 1920x600px para desktop e 768x500px para mobile'
        }),
        ('Configurações de Exibição', {
            'fields': ('ativo', 'ordem', 'data_inicio', 'data_fim')
        }),
    )

class BookAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'autor', 'editora', 'e_lancamento', 'e_destaque', 'tipo_shelf_especial')
    list_filter = ('e_lancamento', 'e_destaque', 'adaptado_filme', 'e_manga', 'tipo_shelf_especial')
    search_fields = ('titulo', 'autor', 'editora')
    ordering = ('titulo',)

    fieldsets = (
        ('Mídia', {
            'fields': ('capa', 'capa_preview'),
            'description': 'Upload de imagens do livro. Tamanho recomendado: 400x600px'
        }),
        ('Informações Básicas', {
            'fields': ('titulo', 'subtitulo', 'autor', 'tradutor', 'ilustrador', 'editora', 'isbn', 'edicao',
                       'data_publicacao', 'numero_paginas', 'idioma', 'formato', 'dimensoes', 'peso', 'preco',
                       'preco_promocional')
        }),
        ('Categorização e Conteúdo', {
            'fields': ('categoria', 'genero', 'descricao', 'temas', 'personagens', 'enredo', 'publico_alvo')
        }),
        ('Metadados e Conteúdo Adicional', {
            'fields': ('premios', 'adaptacoes', 'colecao', 'classificacao', 'localizacao'),
            'classes': ('collapse',)
        }),
        ('Recursos Web e Marketing', {
            'fields': ('website', 'redes_sociais', 'citacoes', 'curiosidades'),
            'classes': ('collapse',)
        }),
        ('Conteúdo Textual', {
            'fields': ('prefacio', 'posfacio', 'notas', 'bibliografia', 'indice', 'glossario', 'apendices'),
            'classes': ('collapse',)
        }),
        ('Configurações da Home', {
            'fields': (
                'e_lancamento', 'quantidade_vendida', 'quantidade_acessos',
                'e_destaque', 'adaptado_filme', 'e_manga', 'tipo_shelf_especial',
                'ordem_exibicao'
            )
        }),
    )

    readonly_fields = ('created_at', 'updated_at')

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('created_at',)
        return self.readonly_fields

class UserBookShelfAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'shelf_type', 'added_at', 'updated_at')  # Substituído 'personal_rating' por 'updated_at'
    list_filter = ('shelf_type', 'added_at')
    search_fields = ('user__username', 'book__titulo')
    raw_id_fields = ('user', 'book')

    fieldsets = (
        ('Informações da Estante', {
            'fields': ('user', 'book', 'shelf_type')
        }),
        ('Datas', {
            'fields': ('added_at', 'updated_at')
        }),
    )

# Registrando os modelos no admin_site personalizado
admin_site.register(User, CustomUserAdmin)
admin_site.register(Profile, ProfileAdmin)
admin_site.register(Book, BookAdmin)
admin_site.register(UserBookShelf, UserBookShelfAdmin)
admin_site.register(Group)  # Registrando o modelo Group do Django
admin_site.register(Banner, BannerAdmin)
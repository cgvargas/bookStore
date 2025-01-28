# cgbookstore/apps/core/admin.py

import os
import logging
from datetime import datetime
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponse
from django.urls import path
from django.core import management
from django.contrib import messages
from django.contrib.auth.models import Group
from django.conf import settings
from .models import User, Profile, Book, UserBookShelf

logger = logging.getLogger(__name__)

class DatabaseAdminSite(admin.AdminSite):
    site_header = 'CG BookStore Admin'
    site_title = 'CG BookStore Admin Portal'
    index_title = 'Administração CG BookStore'


    def generate_schema_view(self, request):
        try:
            # Define o caminho base correto
            base_dir = os.path.dirname(settings.BASE_DIR)
            output_dir = os.path.join(base_dir, 'database_schemas')

            # Garante que o diretório existe
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # Gera o schema do banco
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
            # Define o caminho base correto
            base_dir = os.path.dirname(settings.BASE_DIR)
            output_dir = os.path.join(base_dir, 'project_structure')

            # Garante que o diretório existe
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # Gera a estrutura
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

            # Log adicional para debug
            logger.info(f'Tentando gerar estrutura em: {output_dir}')
            logger.info(f'Arquivo CSV esperado em: {csv_path}')

        except Exception as e:
            logger.error(f'Erro ao gerar estrutura: {str(e)}')
            messages.error(
                request,
                f'Erro ao gerar estrutura do projeto: {str(e)}'
            )
        return HttpResponse('<script>window.history.back()</script>')

    def _clear_folder_content(self, folder_path, folder_name):
        folder_status = {'files_removed': 0, 'errors': []}

        if not os.path.exists(folder_path):
            logger.warning(f'Pasta {folder_name} não encontrada em: {folder_path}')
            return folder_status

        def remove_recursive(path):
            try:
                # Primeiro remove todos os arquivos
                for root, dirs, files in os.walk(path, topdown=False):
                    # Remove arquivos
                    for file in files:
                        try:
                            file_path = os.path.join(root, file)
                            os.chmod(file_path, 0o777)  # Altera permissão
                            os.unlink(file_path)
                            folder_status['files_removed'] += 1
                            logger.info(f'Arquivo removido: {file_path}')
                        except Exception as e:
                            error_msg = f'Erro ao remover arquivo {file}: {str(e)}'
                            folder_status['errors'].append(error_msg)
                            logger.error(error_msg)

                    # Remove diretórios vazios
                    for dir_name in dirs:
                        try:
                            dir_path = os.path.join(root, dir_name)
                            os.chmod(dir_path, 0o777)  # Altera permissão
                            os.rmdir(dir_path)
                            logger.info(f'Pasta removida: {dir_path}')
                        except Exception as e:
                            error_msg = f'Erro ao remover pasta {dir_name}: {str(e)}'
                            folder_status['errors'].append(error_msg)
                            logger.error(error_msg)

            except Exception as e:
                error_msg = f'Erro ao processar {path}: {str(e)}'
                folder_status['errors'].append(error_msg)
                logger.error(error_msg)

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

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('generate-schema/', self.admin_view(self.generate_schema_view), name='generate-schema'),
            path('generate-structure/', self.admin_view(self.generate_structure_view), name='generate-structure'),
            path('clear-folders/all/', self.admin_view(self.clear_folders_view), name='clear-folders'),
            path('clear-folders/schema/', self.admin_view(self.clear_schema_folder_view), name='clear-schema-folder'),
            path('clear-folders/structure/', self.admin_view(self.clear_structure_folder_view),
                 name='clear-structure-folder'),
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

class BookAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'autor', 'editora', 'categoria', 'data_publicacao')  # Removido 'classificacao'
    list_filter = ('categoria',)  # Removido 'classificacao'
    search_fields = ('titulo', 'autor', 'editora')
    ordering = ('titulo',)

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('titulo', 'autor', 'descricao', 'capa')
        }),
        ('Detalhes do Livro', {
            'fields': ('editora', 'data_publicacao', 'categoria')  # Removido 'classificacao'
        }),
    )

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
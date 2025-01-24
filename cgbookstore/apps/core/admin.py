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

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('generate-schema/', self.admin_view(self.generate_schema_view), name='generate-schema'),
            path('generate-structure/', self.admin_view(self.generate_structure_view), name='generate-structure'),
        ]
        return custom_urls + urls

    def generate_schema_view(self, request):
        try:
            management.call_command('generate_tables')
            messages.success(request, 'Schema do banco de dados gerado com sucesso!')
        except Exception as e:
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
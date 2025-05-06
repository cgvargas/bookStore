# cgbookstore/apps/core/admin/user_admin.py
"""
Classes de administração para modelos de usuário e perfil.

Este módulo contém as classes administrativas customizadas para
gerenciar usuários e perfis do sistema.
"""

import logging
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .mixins import LoggingAdminMixin, OptimizedQuerysetMixin

logger = logging.getLogger(__name__)


class CustomUserAdmin(LoggingAdminMixin, BaseUserAdmin):
    """
    Configuração personalizada do admin para usuários.

    Características:
    - Campos de exibição personalizados
    - Fieldsets detalhados
    - Filtros e campos de busca
    """
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

    def has_delete_permission(self, request, obj=None):
        """
        Restringe a exclusão de usuários para evitar exclusões acidentais.
        Apenas superusuários podem excluir usuários.
        """
        if not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)


class ProfileAdmin(LoggingAdminMixin, OptimizedQuerysetMixin, admin.ModelAdmin):
    """
    Configuração do admin para perfis de usuário.

    Incorpora otimizações de consulta para melhorar a performance.
    """
    list_display = ('user', 'location', 'birth_date', 'updated_at')
    search_fields = ('user__username', 'user__email', 'location')
    list_filter = ('updated_at',)
    raw_id_fields = ('user',)

    # Campos para otimização de consultas
    select_related_fields = ['user']

    def get_queryset(self, request):
        """
        Otimiza o queryset para incluir informações de usuário relacionado.
        """
        return super().get_queryset(request).select_related('user')

    def save_model(self, request, obj, form, change):
        """
        Personaliza o comportamento ao salvar um perfil.
        Registra atividade de alteração com detalhes adicionais.
        """
        super().save_model(request, obj, form, change)

        # Log adicional com informações detalhadas
        if change:
            logger.info(
                f"Perfil atualizado - Usuário: {obj.user.username} | "
                f"Atualizado por: {request.user.username}"
            )
        else:
            logger.info(
                f"Perfil criado - Usuário: {obj.user.username} | "
                f"Criado por: {request.user.username}"
            )
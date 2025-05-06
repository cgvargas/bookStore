# cgbookstore/apps/core/admin/custom_section_admin.py
"""
Classes de administração para modelos de seções customizadas.

Este módulo contém as classes administrativas customizadas para
gerenciar tipos de seções, layouts e eventos personalizados.
"""

import logging
from django.contrib import admin
from django.utils.html import format_html

from .. import models
from ..models.home_content import (
    CustomSectionType, CustomSectionLayout, EventItem
)
from .mixins import LoggingAdminMixin, OptimizedQuerysetMixin

logger = logging.getLogger(__name__)


class CustomSectionTypeAdmin(LoggingAdminMixin, admin.ModelAdmin):
    """
    Configuração de admin para tipos de seções customizadas.
    """
    list_display = ('nome', 'identificador', 'ativo', 'created_at')
    list_filter = ('ativo',)
    search_fields = ('nome', 'identificador', 'descricao')
    prepopulated_fields = {'identificador': ('nome',)}
    list_per_page = 20

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'identificador', 'descricao', 'ativo')
        }),
        ('Configurações Avançadas', {
            'fields': ('metadados',),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """
        Registra log detalhado quando um tipo de seção é salvo.
        """
        super().save_model(request, obj, form, change)

        action = "atualizado" if change else "criado"
        logger.info(
            f"Tipo de seção customizada '{obj.nome}' ({obj.identificador}) {action} por {request.user.username}"
        )


class CustomSectionLayoutAdmin(LoggingAdminMixin, admin.ModelAdmin):
    """
    Configuração de admin para layouts de seções customizadas.
    """
    list_display = ('nome', 'section_type', 'identificador', 'template_path', 'ativo', 'preview_imagem')
    list_filter = ('ativo', 'section_type')
    search_fields = ('nome', 'identificador', 'template_path')
    prepopulated_fields = {'identificador': ('nome',)}
    list_per_page = 20

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'identificador', 'section_type', 'ativo')
        }),
        ('Template', {
            'fields': ('template_path',)
        }),
        ('Visualização', {
            'fields': ('imagem_preview',)
        }),
    )

    def preview_imagem(self, obj):
        if obj.imagem_preview:
            return format_html('<img src="{}" width="80" height="45" style="object-fit: cover;" />',
                               obj.imagem_preview.url)
        return "Sem preview"

    preview_imagem.short_description = 'Preview'

    def get_queryset(self, request):
        """Otimiza o queryset para relacionamentos"""
        return super().get_queryset(request).select_related('section_type')


class EventItemInline(admin.TabularInline):
    """
    Inline para eventos dentro de seções customizadas.
    """
    model = EventItem
    extra = 1
    fields = ('titulo', 'data_evento', 'local', 'ordem', 'em_destaque', 'ativo')
    ordering = ['ordem', 'data_evento']


class CustomSectionAdmin(LoggingAdminMixin, OptimizedQuerysetMixin, admin.ModelAdmin):
    """
    Configuração de admin para seções customizadas.
    """
    list_display = ('section', 'section_type', 'layout', 'ativo', 'get_eventos_count')
    list_filter = ('ativo', 'section_type')
    search_fields = ('section__titulo',)
    raw_id_fields = ['section', 'section_type', 'layout']
    inlines = [EventItemInline]

    # Campos para otimização de consultas
    select_related_fields = ['section', 'section_type', 'layout']
    prefetch_related_fields = ['events']

    fieldsets = (
        ('Seção Base', {
            'fields': ('section',),
            'description': 'Selecione a seção base da página inicial'
        }),
        ('Configuração de Tipo e Layout', {
            'fields': ('section_type', 'layout', 'ativo')
        }),
        ('Configurações Adicionais', {
            'fields': ('config_json',),
            'classes': ('collapse',)
        }),
    )

    def get_eventos_count(self, obj):
        return obj.events.count()

    get_eventos_count.short_description = 'Eventos'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        # Filtra os layouts conforme o tipo de seção selecionado
        if obj and obj.section_type:
            form.base_fields['layout'].queryset = CustomSectionLayout.objects.filter(
                section_type=obj.section_type,
                ativo=True
            )

        return form


class EventItemAdmin(LoggingAdminMixin, OptimizedQuerysetMixin, admin.ModelAdmin):
    """
    Configuração de admin para eventos.
    """
    list_display = ('titulo', 'data_evento', 'local', 'ordem', 'em_destaque', 'ativo', 'custom_section')
    list_filter = ('ativo', 'em_destaque', 'custom_section__section_type')
    search_fields = ('titulo', 'descricao', 'local')
    date_hierarchy = 'data_evento'
    list_per_page = 20

    # Campos para otimização de consultas
    select_related_fields = ['custom_section', 'custom_section__section_type']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('titulo', 'descricao', 'imagem')
        }),
        ('Data e Local', {
            'fields': ('data_evento', 'local',)
        }),
        ('Configurações de Exibição', {
            'fields': ('custom_section', 'ordem', 'em_destaque', 'ativo')
        }),
        ('Links', {
            'fields': ('url',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Otimiza a consulta para evitar múltiplas queries"""
        return super().get_queryset(request).select_related(
            'custom_section', 'custom_section__section_type'
        )
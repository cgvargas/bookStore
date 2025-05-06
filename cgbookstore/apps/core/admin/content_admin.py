# cgbookstore/apps/core/admin/content_admin.py
"""
Classes de administração para modelos de conteúdo.

Este módulo contém as classes administrativas customizadas para
gerenciar conteúdos como banners, vídeos e anúncios.
"""

import logging
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from ..models.home_content import (
    VideoSectionItem,
    VideoItem,
    Advertisement,
    LinkGridItem,
    VideoSection,
    BackgroundSettings,
    HomeSection
)

from .mixins import LoggingAdminMixin, OptimizedQuerysetMixin

logger = logging.getLogger(__name__)


class BannerAdmin(LoggingAdminMixin, admin.ModelAdmin):
    """
    Configuração do admin para banners.

    Características:
    - Campos de exibição personalizados
    - Fieldsets detalhados
    - Filtros e ordenação
    """
    list_display = ('titulo', 'ativo', 'ordem', 'data_inicio', 'data_fim', 'imagem_preview')
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

    def imagem_preview(self, obj):
        """Exibe uma prévia da imagem do banner"""
        if obj.imagem:
            return format_html('<img src="{}" height="50" />', obj.imagem.url)
        return "Sem imagem"

    imagem_preview.short_description = 'Prévia'


class LinkGridItemInline(admin.TabularInline):
    """
    Inline para itens de grade de links.
    """
    model = LinkGridItem
    extra = 1
    readonly_fields = ('preview_imagem',)

    def preview_imagem(self, obj):
        if obj.imagem:
            return format_html('<img src="{}" height="50"/>', obj.imagem.url)
        return "Sem imagem"

    preview_imagem.short_description = 'Visualização'


class VideoItemInline(admin.TabularInline):
    """
    Inline para itens de vídeo em seções de vídeo.
    """
    model = VideoSectionItem
    extra = 1
    fields = ('video', 'ordem', 'ativo')
    ordering = ['ordem']


class VideoItemAdmin(LoggingAdminMixin, admin.ModelAdmin):
    """
    Configuração de admin para itens de vídeo individuais.
    """
    list_display = ('titulo', 'url', 'ordem', 'ativo', 'updated_at', 'thumbnail_preview')
    list_filter = ('ativo',)
    search_fields = ('titulo', 'url')
    ordering = ('ordem',)

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('titulo', 'url', 'ordem', 'ativo')
        }),
        ('Imagem', {
            'fields': ('thumbnail',),
            'classes': ('collapse',)
        }),
    )

    def thumbnail_preview(self, obj):
        """Exibe uma prévia da thumbnail do vídeo"""
        if obj.thumbnail:
            return format_html('<img src="{}" height="50" />', obj.thumbnail.url)
        return "Sem thumbnail"

    thumbnail_preview.short_description = 'Thumbnail'


class VideoSectionAdmin(LoggingAdminMixin, OptimizedQuerysetMixin, admin.ModelAdmin):
    """
    Configuração de admin para seções de vídeo.
    """
    list_display = ('get_section_title', 'ativo', 'get_videos_count')
    list_filter = ('ativo',)
    inlines = [VideoItemInline]

    # Campos para otimização de consultas
    select_related_fields = ['section']
    prefetch_related_fields = ['videos']

    def get_section_title(self, obj):
        return obj.section.titulo if obj.section else 'Sem Seção'

    get_section_title.short_description = 'Título da Seção'

    def get_videos_count(self, obj):
        return obj.videos.count() if hasattr(obj, 'videos') else 0

    get_videos_count.short_description = 'Quantidade de Vídeos'

    def get_queryset(self, request):
        """Otimiza o queryset para relacionamentos"""
        return super().get_queryset(request).select_related(
            'section'
        ).prefetch_related('videos')


class AdvertisementAdmin(LoggingAdminMixin, admin.ModelAdmin):
    """
    Configuração de admin para anúncios.
    """
    list_display = ('section', 'get_imagem_preview', 'data_inicio', 'data_fim', 'clicks')
    list_filter = ('data_inicio', 'data_fim')
    search_fields = ('section__titulo',)
    readonly_fields = ('clicks', 'get_imagem_preview')

    def get_imagem_preview(self, obj):
        if obj.imagem:
            return format_html('<img src="{}" height="50"/>', obj.imagem.url)
        return "Sem imagem"

    get_imagem_preview.short_description = 'Visualização'


# Registro inline para BackgroundSettings
class BackgroundSettingsInline(admin.StackedInline):
    model = BackgroundSettings
    can_delete = False
    verbose_name_plural = 'Configuração de Background'
    fk_name = 'section'

    # Garantir que os campos obrigatórios sejam mostrados
    fieldsets = (
        ('Informações Gerais', {
            'fields': ('imagem', 'habilitado')
        }),
        ('Configurações de Exibição', {
            'fields': ('aplicar_em', 'posicao', 'opacidade')
        }),
        ('Informações do Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


# Update no HomeSectionAdmin
class HomeSectionAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'ativo', 'ordem', 'mostrar_configuracao')
    list_filter = ('tipo', 'ativo')
    search_fields = ('titulo',)
    ordering = ('ordem',)
    inlines = []  # Será preenchido dinamicamente

    def get_inlines(self, request, obj=None):
        inlines = super().get_inlines(request, obj)
        # Adiciona o inline apenas para seções do tipo 'background'
        if obj and obj.tipo == 'background':
            inlines.append(BackgroundSettingsInline)
        return inlines

    def mostrar_configuracao(self, obj):
        """Mostra um botão para acessar a configuração específica baseado no tipo"""
        if obj.tipo == 'background':
            try:
                config = obj.background_settings
                url = reverse('admin:core_backgroundsettings_change', args=[config.id])
                return format_html('<a class="button" href="{}">Configurar Background</a>', url)
            except BackgroundSettings.DoesNotExist:
                url = reverse('admin:core_backgroundsettings_add')
                return format_html('<a class="button" href="{}?section={}">Criar Configuração</a>', url, obj.id)
        return "-"

    mostrar_configuracao.short_description = "Configuração"


# Registro independente do BackgroundSettings
class BackgroundSettingsAdmin(admin.ModelAdmin):
    list_display = ('section', 'habilitado', 'aplicar_em', 'posicao', 'opacidade', 'updated_at')
    list_filter = ('habilitado', 'aplicar_em', 'posicao')
    search_fields = ('section__titulo',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Informações Gerais', {
            'fields': ('section', 'imagem', 'habilitado')
        }),
        ('Configurações de Exibição', {
            'fields': ('aplicar_em', 'posicao', 'opacidade')
        }),
        ('Informações do Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
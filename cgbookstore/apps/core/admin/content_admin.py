# Arquivo: cgbookstore/apps/core/admin/content_admin.py

import logging
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count

from ..models.home_content import (
    VideoItem,
    VideoSection,
    VideoSectionItem,
    Advertisement,
    BackgroundSettings,
    LinkGridItem
)
from ..models.author import (
    Author,
    AuthorSection,
    AuthorSectionItem
)
from .mixins import LoggingAdminMixin

logger = logging.getLogger(__name__)


class VideoSectionItemInline(admin.TabularInline):
    model = VideoSectionItem
    extra = 1
    # raw_id_fields = ('video',)  # ← REMOVIDO: Causava problema nos "3 pontinhos" não clicáveis


class VideoSectionInline(admin.StackedInline):
    model = VideoSection
    can_delete = False
    verbose_name_plural = 'Configurações da Seção de Vídeos'
    classes = ('video-options',)


@admin.register(VideoSection)
class VideoSectionAdmin(admin.ModelAdmin):
    list_display = ('section', 'ativo')
    inlines = [VideoSectionItemInline]


class AdvertisementInline(admin.StackedInline):
    model = Advertisement
    can_delete = False
    verbose_name_plural = 'Configurações do Anúncio'
    classes = ('ad-options',)


class BackgroundSettingsInline(admin.StackedInline):
    model = BackgroundSettings
    can_delete = False
    verbose_name_plural = 'Configurações do Background'
    classes = ('background-options',)


class LinkGridItemInline(admin.TabularInline):
    model = LinkGridItem
    extra = 1
    verbose_name_plural = 'Itens da Grade de Links'
    classes = ('link_grid-options',)


# === NOVAS CLASSES PARA AUTHORSECTION ===

class AuthorSectionItemInline(admin.TabularInline):
    """Inline para gerenciar autores em uma seção"""
    model = AuthorSectionItem
    extra = 1
    autocomplete_fields = ('author',)
    ordering = ('ordem',)
    verbose_name = 'Autor da Seção'
    verbose_name_plural = 'Autores da Seção'

    fields = ('author', 'ordem')

    def get_queryset(self, request):
        """Otimiza queryset com select_related"""
        return super().get_queryset(request).select_related('author')


@admin.register(AuthorSection)
class AuthorSectionAdmin(LoggingAdminMixin, admin.ModelAdmin):
    """Interface administrativa para Seções de Autores"""

    list_display = (
        'section_title',
        'max_autores',
        'ordem_exibicao',
        'apenas_destaque',
        'autores_count',
        'ativo_display',
        'updated_at'
    )

    list_filter = (
        'ativo',
        'apenas_destaque',
        'ordem_exibicao',
        'section__ativo'
    )

    search_fields = (
        'section__titulo',
        'titulo_secundario',
        'descricao',
        'autores__nome',
        'autores__sobrenome'
    )

    autocomplete_fields = ('section',)

    inlines = [AuthorSectionItemInline]

    fieldsets = (
        ('Configuração da Seção', {
            'fields': ('section', 'titulo_secundario', 'descricao')
        }),
        ('Configurações de Exibição', {
            'fields': (
                'mostrar_biografia',
                'apenas_destaque',
                'max_autores',
                'ordem_exibicao'
            ),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('ativo',),
            'classes': ('collapse',)
        })
    )

    ordering = ('-updated_at',)

    def get_queryset(self, request):
        """Otimiza queryset com relacionamentos"""
        return super().get_queryset(request).select_related(
            'section'
        ).prefetch_related(
            'autores'
        ).annotate(
            total_autores=Count('autores')
        )

    def section_title(self, obj):
        """Exibe título da seção relacionada"""
        return obj.section.titulo

    section_title.short_description = 'Seção'
    section_title.admin_order_field = 'section__titulo'

    def autores_count(self, obj):
        """Exibe quantidade de autores na seção"""
        if hasattr(obj, 'total_autores'):
            return obj.total_autores
        return obj.autores.count()

    autores_count.short_description = 'Qtd. Autores'
    autores_count.admin_order_field = 'total_autores'

    def ativo_display(self, obj):
        """Exibe status com ícone colorido"""
        if obj.ativo:
            return format_html(
                '<span style="color: green;">●</span> Ativo'
            )
        return format_html(
            '<span style="color: red;">●</span> Inativo'
        )

    ativo_display.short_description = 'Status'
    ativo_display.admin_order_field = 'ativo'

    def get_form(self, request, obj=None, **kwargs):
        """Customiza formulário baseado em permissões"""
        form = super().get_form(request, obj, **kwargs)

        # Filtrar apenas HomeSection do tipo 'author'
        if 'section' in form.base_fields:
            form.base_fields['section'].queryset = form.base_fields['section'].queryset.filter(
                tipo='author'
            )

        return form

    actions = ['ativar_secoes', 'desativar_secoes']

    def ativar_secoes(self, request, queryset):
        """Ação para ativar seções selecionadas"""
        updated = queryset.update(ativo=True)
        self.message_user(
            request,
            f'{updated} seção(ões) de autores foram ativadas.'
        )

    ativar_secoes.short_description = 'Ativar seções selecionadas'

    def desativar_secoes(self, request, queryset):
        """Ação para desativar seções selecionadas"""
        updated = queryset.update(ativo=False)
        self.message_user(
            request,
            f'{updated} seção(ões) de autores foram desativadas.'
        )

    desativar_secoes.short_description = 'Desativar seções selecionadas'


@admin.register(VideoItem)
class VideoItemAdmin(LoggingAdminMixin, admin.ModelAdmin):
    list_display = ('titulo', 'url', 'ordem', 'ativo', 'thumbnail_preview')
    list_filter = ('ativo',)
    search_fields = ('titulo', 'url')
    ordering = ('ordem',)

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" height="50" />', obj.thumbnail.url)
        return "Sem thumbnail"

    thumbnail_preview.short_description = 'Thumbnail'
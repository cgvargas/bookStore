"""
Classes de administração para o modelo Author.

Este módulo contém as classes administrativas customizadas para
gerenciar autores e suas seções.
"""

import logging
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count

from ..models.author import Author, AuthorSection, AuthorSectionItem
from .mixins import LoggingAdminMixin, OptimizedQuerysetMixin

logger = logging.getLogger(__name__)


class AuthorSectionItemInline(admin.TabularInline):
    """Inline para gerenciar itens de seções de autores"""
    model = AuthorSectionItem
    extra = 1
    verbose_name = 'Item de Autor'
    verbose_name_plural = 'Itens de Autores'
    fields = ('author', 'ordem')
    autocomplete_fields = ['author']


class AuthorSectionAdmin(LoggingAdminMixin, admin.ModelAdmin):
    """Configuração administrativa para seções de autores"""
    list_display = ('section', 'titulo_secundario', 'max_autores', 'ordem_exibicao', 'ativo')
    list_filter = ('ativo', 'ordem_exibicao', 'apenas_destaque')
    search_fields = ('section__titulo', 'titulo_secundario', 'descricao')
    inlines = [AuthorSectionItemInline]


class AuthorAdmin(LoggingAdminMixin, OptimizedQuerysetMixin, admin.ModelAdmin):
    """
    Classe administrativa customizada para o modelo Author.
    """
    list_display = ('nome_completo', 'nacionalidade', 'destaque', 'ativo', 'foto_preview', 'get_livros_count')
    list_filter = ('destaque', 'ativo', 'nacionalidade')
    search_fields = ('nome', 'sobrenome', 'biografia', 'nacionalidade')
    prepopulated_fields = {'slug': ('nome', 'sobrenome')}
    readonly_fields = ('created_at', 'updated_at', 'foto_preview')
    list_editable = ('destaque', 'ativo')
    actions = ['mark_as_featured', 'remove_featured', 'activate_authors', 'deactivate_authors']

    # Otimizações de consulta
    prefetch_related_fields = ['books']

    fieldsets = (
        ('Informações Básicas', {
            'fields': (('nome', 'sobrenome'), 'slug', 'nacionalidade', 'data_nascimento')
        }),
        ('Biografia e Mídia', {
            'fields': ('biografia', 'foto', 'foto_preview')
        }),
        ('Web e Redes Sociais', {
            'fields': ('website', 'twitter', 'instagram', 'facebook'),
            'classes': ('collapse',)
        }),
        ('Exibição', {
            'fields': ('destaque', 'ordem', 'ativo')
        }),
        ('Informações do Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def nome_completo(self, obj):
        """Retorna o nome completo do autor"""
        return obj.get_nome_completo()

    nome_completo.short_description = 'Nome Completo'

    def foto_preview(self, obj):
        """Retorna uma prévia da foto do autor para exibição no admin"""
        if obj.foto:
            return format_html('<img src="{}" height="100" />', obj.foto.url)
        return "Sem foto"

    foto_preview.short_description = 'Prévia da Foto'

    def get_livros_count(self, obj):
        """Retorna o número de livros deste autor"""
        return obj.get_livros_count()

    get_livros_count.short_description = 'Livros'

    # Ações em lote
    def mark_as_featured(self, request, queryset):
        """Marca autores selecionados como destaque"""
        queryset.update(destaque=True)
        self.message_user(request, f"{queryset.count()} autor(es) marcado(s) como destaque.")

    mark_as_featured.short_description = "Marcar como destaque"

    def remove_featured(self, request, queryset):
        """Remove autores selecionados do destaque"""
        queryset.update(destaque=False)
        self.message_user(request, f"{queryset.count()} autor(es) removido(s) do destaque.")

    remove_featured.short_description = "Remover do destaque"

    def activate_authors(self, request, queryset):
        """Ativa autores selecionados"""
        queryset.update(ativo=True)
        self.message_user(request, f"{queryset.count()} autor(es) ativado(s).")

    activate_authors.short_description = "Ativar autores"

    def deactivate_authors(self, request, queryset):
        """Desativa autores selecionados"""
        queryset.update(ativo=False)
        self.message_user(request, f"{queryset.count()} autor(es) desativado(s).")

    deactivate_authors.short_description = "Desativar autores"
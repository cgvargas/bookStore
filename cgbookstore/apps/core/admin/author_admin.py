# Arquivo: cgbookstore/apps/core/admin/author_admin.py

import logging
from django.contrib import admin
from django.utils.html import format_html

# Importação dos modelos necessários
from ..models.author import Author, AuthorSection, AuthorSectionItem
from ..models.home_content import HomeSection # Importação adicional
from .mixins import LoggingAdminMixin, OptimizedQuerysetMixin

logger = logging.getLogger(__name__)


class AuthorSectionItemInline(admin.TabularInline):
    model = AuthorSectionItem
    extra = 1
    verbose_name = 'Autor na Seção'
    verbose_name_plural = 'Autores na Seção'
    fields = ('author', 'ordem')
    autocomplete_fields = ['author']


class AuthorSectionInline(admin.StackedInline):
    model = AuthorSection
    # Isso remove a necessidade de criar a HomeSection separadamente
    can_delete = False
    verbose_name_plural = 'Configurações da Seção de Autores'
    fieldsets = (
        (None, {
            'fields': (
                'titulo_secundario',
                'descricao',
                ('ordem_exibicao', 'max_autores'),
                ('mostrar_biografia', 'apenas_destaque', 'ativo'),
            )
        }),
    )
    classes = ('author-options',)
    inlines = [AuthorSectionItemInline]


@admin.register(Author)
class AuthorAdmin(LoggingAdminMixin, OptimizedQuerysetMixin, admin.ModelAdmin):
    list_display = ('nome_completo', 'nacionalidade', 'destaque', 'ativo', 'foto_preview', 'get_livros_count')
    list_filter = ('destaque', 'ativo', 'nacionalidade')
    search_fields = ('nome', 'sobrenome', 'biografia', 'nacionalidade')
    prepopulated_fields = {'slug': ('nome', 'sobrenome')}
    readonly_fields = ('created_at', 'updated_at', 'foto_preview')
    list_editable = ('destaque', 'ativo')
    actions = ['mark_as_featured', 'remove_featured', 'activate_authors', 'deactivate_authors']
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
        return obj.get_nome_completo()
    nome_completo.short_description = 'Nome Completo'

    def foto_preview(self, obj):
        if obj.foto:
            return format_html('<img src="{}" height="100" />', obj.foto.url)
        return "Sem foto"
    foto_preview.short_description = 'Prévia da Foto'

    def get_livros_count(self, obj):
        return obj.get_livros_count()
    get_livros_count.short_description = 'Livros'

    def mark_as_featured(self, request, queryset):
        queryset.update(destaque=True)
        self.message_user(request, f"{queryset.count()} autor(es) marcado(s) como destaque.")
    mark_as_featured.short_description = "Marcar como destaque"

    def remove_featured(self, request, queryset):
        queryset.update(destaque=False)
        self.message_user(request, f"{queryset.count()} autor(es) removido(s) do destaque.")
    remove_featured.short_description = "Remover do destaque"

    def activate_authors(self, request, queryset):
        queryset.update(ativo=True)
        self.message_user(request, f"{queryset.count()} autor(es) ativado(s).")
    activate_authors.short_description = "Ativar autores"

    def deactivate_authors(self, request, queryset):
        queryset.update(ativo=False)
        self.message_user(request, f"{queryset.count()} autor(es) desativado(s).")
    deactivate_authors.short_description = "Desativar autores"
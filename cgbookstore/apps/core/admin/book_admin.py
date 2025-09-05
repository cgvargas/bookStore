# cgbookstore/apps/core/admin/book_admin.py
"""
Classes de administração para o modelo Book.

Este módulo contém as classes administrativas customizadas para
gerenciar livros e suas categorias.
"""

import logging
from django.contrib import admin
from django.utils.html import format_html

from ..models.book import Book, BookAuthor
from .forms import BookAdminForm
from .mixins import LoggingAdminMixin, OptimizedQuerysetMixin

logger = logging.getLogger(__name__)


class BookAuthorInline(admin.TabularInline):
    """Inline para gerenciar autores de um livro"""
    model = BookAuthor
    extra = 1
    fk_name = 'book'
    verbose_name = 'Autor'
    verbose_name_plural = 'Autores'
    fields = ('author', 'role', 'is_primary')
    autocomplete_fields = ['author']


@admin.register(Book)
class BookAdmin(LoggingAdminMixin, OptimizedQuerysetMixin, admin.ModelAdmin):
    """
    Classe administrativa customizada para o modelo Book.

    Inclui funcionalidades como:
    - Formulário personalizado com validação de campos
    - Fieldsets organizados para melhor visualização
    - Ações em lote para classificação de livros
    - Exibição de métricas e estatísticas
    """
    form = BookAdminForm
    list_display = ('titulo', 'autor', 'editora', 'preco_display', 'e_destaque',
                    'quantidade_acessos', 'quantidade_vendida', 'cover_preview')
    list_filter = ('e_lancamento', 'e_destaque', 'adaptado_filme', 'e_manga', 'created_at')
    search_fields = (
        'titulo',
        'subtitulo',
        'editora',
        'isbn',
        'authors__nome',
        'authors__sobrenome'
    )

    autocomplete_fields = ('authors',)

    readonly_fields = ('quantidade_acessos', 'quantidade_vendida', 'cover_preview',
                       'created_at', 'updated_at')
    list_editable = ('e_destaque',)
    inlines = [BookAuthorInline]  # Adicionamos o inline para autores
    # Adicionada a ação delete_selected para habilitar deleção em massa
    actions = ['delete_selected', 'mark_as_featured', 'remove_featured', 'mark_as_movie_adaptation',
               'remove_movie_adaptation', 'mark_as_new_release', 'remove_new_release']

    # Otimizações de consulta
    select_related_fields = []
    prefetch_related_fields = ['authors']

    # Organização visual dos campos
    fieldsets = (
        ('Informações Básicas', {
            'fields': (('titulo', 'subtitulo'), 'descricao')
        }),
        ('Informações Bibliográficas', {
            'fields': ('autor', 'tradutor', 'ilustrador', 'editora', 'isbn', 'edicao',
                       'data_publicacao', 'numero_paginas', 'categoria', 'genero')
        }),
        ('Características Físicas', {
            'fields': ('formato', 'dimensoes', 'peso', 'idioma'),
            'classes': ('collapse',)
        }),
        ('Preço e Comercialização', {
            'fields': (('preco', 'preco_promocional'), 'localizacao')
        }),
        ('Conteúdo Detalhado', {
            'fields': ('temas', 'personagens', 'enredo', 'publico_alvo'),
            'classes': ('collapse',)
        }),
        ('Metadados Adicionais', {
            'fields': ('premios', 'adaptacoes', 'colecao', 'classificacao'),
            'classes': ('collapse',)
        }),
        ('Mídia', {
            'fields': ('capa', 'capa_preview', 'capa_url', 'cover_preview'),
        }),
        ('Integração Externa', {
            'fields': ('external_id', 'is_temporary', 'origem', 'external_data'),
            'classes': ('collapse',)
        }),
        ('Web e Marketing', {
            'fields': ('website', 'redes_sociais', 'citacoes', 'curiosidades'),
            'classes': ('collapse',)
        }),
        ('Exibição na Home', {
            'fields': ('e_lancamento', 'e_destaque', 'adaptado_filme', 'e_manga',
                       'ordem_exibicao', 'tipo_shelf_especial')
        }),
        ('Métricas', {
            'fields': ('quantidade_acessos', 'quantidade_vendida'),
            'classes': ('collapse',)
        }),
        ('Informações do Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def cover_preview(self, obj):
        """Retorna uma prévia da capa do livro para exibição no admin"""
        if obj.capa:
            return format_html('<img src="{}" height="100" />', obj.get_display_cover_url())
        return "Sem capa"

    cover_preview.short_description = 'CAPA'

    def preco_display(self, obj):
        """Formata o preço para exibição na lista"""
        if obj.preco is None:
            return '-'

        try:
            # Converter para float para garantir compatibilidade com o formato {:.2f}
            preco = float(obj.preco)

            if obj.preco_promocional is not None:
                preco_promocional = float(obj.preco_promocional)
                return format_html('<span style="text-decoration: line-through">R$ {:.2f}</span> '
                                   '<span style="color: green">R$ {:.2f}</span>',
                                   preco, preco_promocional)

            # Se não houver preço promocional, retorna apenas o preço normal
            return format_html('R$ {:.2f}', preco)

        except (TypeError, ValueError):
            # Em caso de erro na conversão
            return "Preço inválido"

    preco_display.short_description = 'PREÇO'

    # Adicionando short_description para campos do modelo
    def get_changelist_form(self, request, **kwargs):
        """Customiza o formulário da changelist"""
        form = super().get_changelist_form(request, **kwargs)
        return form

    def get_changelist_formset(self, request, **kwargs):
        """Customiza o formset da changelist"""
        formset = super().get_changelist_formset(request, **kwargs)
        return formset

    # Customizar labels dos campos do modelo
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customizar títulos das colunas diretamente nos campos do modelo
        if hasattr(Book, 'quantidade_acessos'):
            Book._meta.get_field('quantidade_acessos').verbose_name = 'ACESSOS'
        if hasattr(Book, 'quantidade_vendida'):
            Book._meta.get_field('quantidade_vendida').verbose_name = 'VENDAS'

    # Ações em lote
    def mark_as_featured(self, request, queryset):
        """Marca livros selecionados como destaque"""
        queryset.update(e_destaque=True)
        self.message_user(request, f"{queryset.count()} livro(s) marcado(s) como destaque.")

    mark_as_featured.short_description = "Marcar como destaque"

    def remove_featured(self, request, queryset):
        """Remove livros selecionados do destaque"""
        queryset.update(e_destaque=False)
        self.message_user(request, f"{queryset.count()} livro(s) removido(s) do destaque.")

    remove_featured.short_description = "Remover do destaque"

    def mark_as_movie_adaptation(self, request, queryset):
        """Marca livros selecionados como adaptados para filme/série"""
        queryset.update(adaptado_filme=True)
        self.message_user(request, f"{queryset.count()} livro(s) marcado(s) como adaptado(s) para filme/série.")

    mark_as_movie_adaptation.short_description = "Marcar como adaptado para filme/série"

    def remove_movie_adaptation(self, request, queryset):
        """Remove livros selecionados da marcação de adaptado para filme/série"""
        queryset.update(adaptado_filme=False)
        self.message_user(request, f"{queryset.count()} livro(s) removido(s) da marcação de adaptado para filme/série.")

    remove_movie_adaptation.short_description = "Remover marcação de adaptado para filme/série"

    def mark_as_new_release(self, request, queryset):
        """Marca livros selecionados como lançamentos"""
        queryset.update(e_lancamento=True)
        self.message_user(request, f"{queryset.count()} livro(s) marcado(s) como lançamento.")

    mark_as_new_release.short_description = "Marcar como lançamento"

    def remove_new_release(self, request, queryset):
        """Remove livros selecionados da marcação de lançamento"""
        queryset.update(e_lancamento=False)
        self.message_user(request, f"{queryset.count()} livro(s) removido(s) da marcação de lançamento.")

    remove_new_release.short_description = "Remover marcação de lançamento"

    def get_queryset(self, request):
        """Otimiza o queryset com prefetch_related para os autores"""
        return super().get_queryset(request).prefetch_related('authors')
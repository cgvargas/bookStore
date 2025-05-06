# cgbookstore/apps/core/admin/shelf_admin.py
"""
Classes de administração para modelos de prateleiras.

Este módulo contém as classes administrativas customizadas para
gerenciar tipos de prateleiras, seções e conteúdo relacionado.
"""

import logging
from django.contrib import admin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

from ..models.home_content import (
    HomeSection, BookShelfSection, BookShelfItem,
    DefaultShelfType
)
from .forms import BookShelfSectionAdminForm
from .mixins import (
    LoggingAdminMixin, OptimizedQuerysetMixin,
    HelpTextAdminMixin
)

logger = logging.getLogger(__name__)


class BookShelfItemInline(admin.TabularInline):
    """
    Inline para gerenciar itens de prateleira dentro do admin de prateleiras.
    """
    model = BookShelfItem
    extra = 1
    raw_id_fields = ('livro',)
    readonly_fields = ('added_at',)
    classes = ('collapse',)

    def get_queryset(self, request):
        """
        Otimiza o queryset para relacionamentos.
        """
        return super().get_queryset(request).select_related('livro').order_by('ordem')


class UserBookShelfAdmin(LoggingAdminMixin, OptimizedQuerysetMixin, admin.ModelAdmin):
    """
    Configuração do admin para prateleiras de usuário.
    """
    list_display = ('user', 'book', 'shelf_type', 'added_at', 'updated_at')
    list_filter = ('shelf_type', 'added_at')
    search_fields = ('user__username', 'book__titulo')
    raw_id_fields = ('user', 'book')
    readonly_fields = ('added_at', 'updated_at')

    # Definir explicitamente apenas campos editáveis
    fields = ('user', 'book', 'shelf_type')

    # Campos para otimização de consultas
    select_related_fields = ['user', 'book']


class HomeSectionAdmin(LoggingAdminMixin, admin.ModelAdmin):
    """
    Interface administrativa para gerenciar seções da página inicial.
    Inclui ações para facilitar a criação de prateleiras associadas.
    """
    list_display = ('titulo', 'tipo', 'ordem', 'ativo', 'prateleira_status', 'updated_at')
    list_filter = ('tipo', 'ativo')
    search_fields = ('titulo', 'descricao')
    ordering = ('ordem',)
    actions = ['create_book_shelf']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('titulo', 'tipo', 'descricao')
        }),
        ('Configurações de Exibição', {
            'fields': ('ordem', 'ativo', 'css_class')
        }),
    )

    def prateleira_status(self, obj):
        """Verifica se a seção já tem uma prateleira associada"""
        if obj.tipo != 'shelf':
            return False
        return bool(hasattr(obj, 'book_shelf'))

    prateleira_status.short_description = 'Tem Prateleira'
    prateleira_status.boolean = True

    def create_book_shelf(self, request, queryset):
        """Ação para criar prateleiras para seções selecionadas"""
        created_count = 0
        skipped_count = 0

        for section in queryset:
            if section.tipo != 'shelf':
                skipped_count += 1
                continue

            if hasattr(section, 'book_shelf'):
                skipped_count += 1
                continue

            # Cria uma prateleira para esta seção
            BookShelfSection.objects.create(
                section=section,
                max_livros=12
            )
            created_count += 1

        if created_count:
            self.message_user(
                request,
                f"Prateleiras criadas com sucesso para {created_count} seção(ões)."
            )

        if skipped_count:
            self.message_user(
                request,
                f"{skipped_count} seção(ões) ignorada(s) por não serem do tipo 'shelf' ou já terem prateleira.",
                level=messages.WARNING
            )

    create_book_shelf.short_description = "Criar prateleiras para seções selecionadas"

    def save_model(self, request, obj, form, change):
        """Após salvar uma seção do tipo shelf, sugere criar prateleira"""
        super().save_model(request, obj, form, change)

        # Se for uma nova seção do tipo shelf, sugere criar prateleira
        if not change and obj.tipo == 'shelf' and not hasattr(obj, 'book_shelf'):
            messages.info(
                request,
                f'Seção "{obj.titulo}" criada com sucesso. Você pode criar uma prateleira para ela agora: '
                f'<a href="{reverse("admin:core_bookshelfsection_add")}?section={obj.id}" class="button">Criar Prateleira</a>',
                extra_tags='safe'
            )


class BookShelfSectionAdmin(LoggingAdminMixin, HelpTextAdminMixin, OptimizedQuerysetMixin, admin.ModelAdmin):
    """
    Configuração do admin para prateleiras de livros.

    Permite associar seções com tipos de prateleiras personalizadas
    e adicionar livros específicos a cada prateleira.
    """
    form = BookShelfSectionAdminForm
    list_display = ('section', 'get_shelf_type_display', 'max_livros')
    list_filter = ('shelf_type',)
    search_fields = ('section__titulo',)
    inlines = [BookShelfItemInline]

    # Campos para otimização de consultas
    select_related_fields = ['section', 'shelf_type']
    prefetch_related_fields = ['bookshelfitem_set', 'bookshelfitem_set__livro']

    fieldsets = (
        ('Configurações da Prateleira', {
            'fields': ('section', 'shelf_type', 'tipo_shelf', 'max_livros')
        }),
    )

    def get_shelf_type_display(self, obj):
        """Exibe o nome do tipo de prateleira personalizada"""
        if obj.shelf_type:
            return obj.shelf_type.nome
        elif obj.tipo_shelf:
            return dict(obj.SHELF_TYPES).get(obj.tipo_shelf, obj.tipo_shelf)
        return '-'

    get_shelf_type_display.short_description = 'Tipo de Prateleira'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filtra os tipos de prateleira para mostrar apenas os ativos"""
        if db_field.name == "shelf_type":
            kwargs["queryset"] = DefaultShelfType.objects.filter(ativo=True).order_by('ordem')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class DefaultShelfTypeAdmin(LoggingAdminMixin, admin.ModelAdmin):
    """
    Interface administrativa para gerenciar tipos de prateleiras padrão.
    Inclui ações para criar prateleiras e visualizar livros.
    """
    list_display = ('nome', 'identificador', 'filtro_campo', 'get_books_count', 'ordem', 'ativo')
    list_filter = ('ativo', 'filtro_campo')
    search_fields = ('nome', 'identificador')
    ordering = ('ordem',)
    actions = ['create_home_section', 'view_books']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'identificador', 'ordem', 'ativo')
        }),
        ('Configurações de Filtro', {
            'fields': ('filtro_campo', 'filtro_valor'),
            'description': 'Define como os livros serão filtrados para esta prateleira'
        }),
    )

    def get_books_count(self, obj):
        """Retorna a quantidade de livros que correspondem a este tipo de prateleira"""
        try:
            return obj.get_livros().count()
        except Exception:
            return 0

    get_books_count.short_description = 'Qtd. Livros'

    def create_home_section(self, request, queryset):
        """Cria seções da home para os tipos de prateleira selecionados"""
        created_count = 0

        for shelf_type in queryset:
            # Verifica se já existe uma seção com este identificador
            existing = HomeSection.objects.filter(
                book_shelf__shelf_type=shelf_type
            ).first()

            if existing:
                continue

            # Cria uma nova seção
            section = HomeSection.objects.create(
                titulo=shelf_type.nome,
                tipo='shelf',
                ordem=shelf_type.ordem,
                ativo=shelf_type.ativo
            )

            # Cria a prateleira associada
            BookShelfSection.objects.create(
                section=section,
                shelf_type=shelf_type,
                max_livros=12
            )

            created_count += 1

        if created_count:
            self.message_user(
                request,
                f"Criadas {created_count} seções com prateleiras para os tipos selecionados."
            )
        else:
            self.message_user(
                request,
                "Nenhuma seção criada. Talvez já existam seções para todos os tipos selecionados.",
                level=messages.WARNING
            )

    create_home_section.short_description = "Criar seções na home para tipos selecionados"

    def view_books(self, request, queryset):
        """Redireciona para uma lista filtrada de livros que correspondem a este tipo"""
        if queryset.count() != 1:
            self.message_user(
                request,
                "Selecione apenas um tipo de prateleira para ver os livros.",
                level=messages.WARNING
            )
            return

        shelf_type = queryset.first()

        try:
            # Cria uma URL de filtro para a lista de livros
            if shelf_type.filtro_campo == 'e_lancamento':
                return redirect(f"{reverse('admin:core_book_changelist')}?e_lancamento__exact=1")
            elif shelf_type.filtro_campo == 'e_destaque':
                return redirect(f"{reverse('admin:core_book_changelist')}?e_destaque__exact=1")
            elif shelf_type.filtro_campo == 'adaptado_filme':
                return redirect(f"{reverse('admin:core_book_changelist')}?adaptado_filme__exact=1")
            elif shelf_type.filtro_campo == 'e_manga':
                return redirect(f"{reverse('admin:core_book_changelist')}?e_manga__exact=1")
            else:
                # Filtro genérico
                return redirect(reverse('admin:core_book_changelist'))
        except Exception as e:
            self.message_user(
                request,
                f"Erro ao redirecionar: {str(e)}",
                level=messages.ERROR
            )

    view_books.short_description = "Ver livros deste tipo"
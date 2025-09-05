# cgbookstore/apps/core/admin/shelf_admin.py

from django.contrib import admin
from django.forms import ModelForm
from ..models.home_content import HomeSection, HomeSectionBookItem
from ..models.author import AuthorSection
from ..models.home_content import VideoSection, Advertisement, BackgroundSettings

from .author_admin import AuthorSectionInline
from .content_admin import (
    VideoSectionInline,
    AdvertisementInline,
    BackgroundSettingsInline,
    LinkGridItemInline
)


class HomeSectionBookItemInline(admin.TabularInline):
    model = HomeSectionBookItem
    extra = 1
    autocomplete_fields = ['book']
    verbose_name = "Livro Manual"
    verbose_name_plural = "Livros Selecionados Manualmente"
    classes = ('manual-books-inline',)


class HomeSectionAdminForm(ModelForm):
    """Form customizado para HomeSection com correções de dropdown"""

    class Meta:
        model = HomeSection
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Garantir que os campos de choice tenham widgets apropriados
        if 'tipo' in self.fields:
            self.fields['tipo'].widget.attrs.update({
                'class': 'form-control dropdown-fix',
                'style': 'min-width: 300px; white-space: normal;'
            })

        if 'shelf_behavior' in self.fields:
            self.fields['shelf_behavior'].widget.attrs.update({
                'class': 'form-control dropdown-fix',
                'style': 'min-width: 300px; white-space: normal;'
            })


@admin.register(HomeSection)
class HomeSectionAdmin(admin.ModelAdmin):
    form = HomeSectionAdminForm

    list_display = ('titulo', 'tipo', 'ativo', 'ordem')
    list_filter = ('tipo', 'ativo')
    search_fields = ('titulo',)
    list_editable = ('ativo', 'ordem')
    ordering = ('ordem', 'titulo')

    fieldsets = (
        ('Informações Gerais', {
            'fields': ('titulo', 'tipo', 'ativo', 'ordem'),
            'classes': ('wide',)
        }),
        ('Configurações da Prateleira de Livros', {
            'classes': ('shelf-options', 'wide'),
            'fields': ('shelf_behavior', 'shelf_filter_field', 'shelf_filter_value', 'max_books'),
            'description': 'Configure como os livros serão exibidos nesta seção.'
        }),
        ('Aparência e Personalização', {
            'classes': ('collapse', 'wide'),
            'fields': ('css_class', 'customization_options'),
            'description': 'Opções avançadas de personalização visual.'
        }),
    )

    inlines = [
        HomeSectionBookItemInline,
        AuthorSectionInline,
        VideoSectionInline,
        AdvertisementInline,
        BackgroundSettingsInline,
        LinkGridItemInline,
    ]

    class Media:
        js = ('admin/js/home_section_admin.js',)
        css = {
            'all': ('admin/css/home_section_admin.css',)
        }

    # Método get_queryset removido para evitar erros de relacionamento

    def save_model(self, request, obj, form, change):
        """Salva o modelo e cria objetos relacionados conforme necessário"""
        super().save_model(request, obj, form, change)

        # Criar objetos relacionados automaticamente baseado no tipo
        try:
            if obj.tipo == 'video' and not hasattr(obj, 'video_section'):
                VideoSection.objects.create(section=obj)
            elif obj.tipo == 'author' and not hasattr(obj, 'author_section'):
                AuthorSection.objects.create(section=obj)
            elif obj.tipo == 'ad' and not hasattr(obj, 'advertisement'):
                Advertisement.objects.create(section=obj)
            elif obj.tipo == 'background' and not hasattr(obj, 'background_settings'):
                BackgroundSettings.objects.create(section=obj)
        except Exception as e:
            # Log do erro sem quebrar o fluxo
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Erro ao criar objeto relacionado para HomeSection {obj.pk}: {e}")

    def response_change(self, request, obj):
        """Customiza o redirecionamento após salvar"""
        response = super().response_change(request, obj)

        # Remove filtros problemáticos da URL
        if hasattr(response, 'url') and response.url:
            # Limpa parâmetros de filtro corrompidos
            if '_changelist_filters=' in response.url:
                from django.urls import reverse
                response.url = reverse('admin:core_homesection_changelist')

        return response

    def response_add(self, request, obj, post_url_continue=None):
        """Customiza o redirecionamento após adicionar"""
        response = super().response_add(request, obj, post_url_continue)

        # Remove filtros problemáticos da URL
        if hasattr(response, 'url') and response.url:
            if '_changelist_filters=' in response.url:
                from django.urls import reverse
                response.url = reverse('admin:core_homesection_changelist')

        return response

    def changelist_view(self, request, extra_context=None):
        """Customiza a view da lista para limpar filtros corrompidos"""
        # Limpa filtros corrompidos da sessão
        if hasattr(request, 'session'):
            session_key = f'admin:core:homesection:changelist:filters'
            if session_key in request.session:
                try:
                    # Verifica se os filtros estão corrompidos
                    filters = request.session[session_key]
                    if not isinstance(filters, dict):
                        del request.session[session_key]
                except (KeyError, ValueError, TypeError):
                    # Remove filtros corrompidos
                    request.session.pop(session_key, None)

        return super().changelist_view(request, extra_context)
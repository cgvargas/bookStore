# Arquivo: cgbookstore/apps/core/admin/__init__.py

import logging
from django.contrib.auth.models import Group

# Importações de Modelos (Estrutura Completa)
from ..models import (
    User, Profile, Book, UserBookShelf, Banner, Author, AuthorSection,
    HomeSection, HomeSectionBookItem, VideoSection, Advertisement, VideoItem,
    CustomSectionType, CustomSectionLayout, CustomSection, EventItem,
    BackgroundSettings, LinkGridItem, VideoSectionItem
)

# Importações de Classes de Administração
from .site import DatabaseAdminSite
from .user_admin import CustomUserAdmin, ProfileAdmin, UserBookShelfAdmin
from .book_admin import BookAdmin
from .author_admin import AuthorAdmin
from .shelf_admin import HomeSectionAdmin
from .content_admin import VideoItemAdmin, VideoSectionAdmin, AuthorSectionAdmin
from .custom_section_admin import (
    CustomSectionTypeAdmin, CustomSectionLayoutAdmin,
    CustomSectionAdmin, EventItemAdmin
)

logger = logging.getLogger(__name__)

from django.contrib import admin


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    """Admin básico para gerenciar banners do carrossel"""
    list_display = ('titulo', 'ativo', 'ordem', 'data_inicio', 'data_fim')
    list_filter = ('ativo', 'data_inicio', 'data_fim')
    search_fields = ('titulo', 'subtitulo', 'descricao')
    list_editable = ('ativo', 'ordem')
    ordering = ['ordem', '-data_inicio']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('titulo', 'subtitulo', 'descricao', 'link')
        }),
        ('Imagens', {
            'fields': ('imagem', 'imagem_mobile')
        }),
        ('Configurações de Exibição', {
            'fields': ('ordem', 'ativo', 'data_inicio', 'data_fim')
        }),
    )


# Instanciação do Site Administrativo Personalizado
admin_site = DatabaseAdminSite(name='admin')

# ==============================================================================
# REGISTRO CENTRALIZADO DE MODELOS
# ==============================================================================

# Seção Principal de Conteúdo
admin_site.register(Book, BookAdmin)
admin_site.register(Author, AuthorAdmin)
admin_site.register(AuthorSection, AuthorSectionAdmin)  # ← ADICIONADO
admin_site.register(Banner, BannerAdmin)

# Seção de Usuários e Autenticação
admin_site.register(User, CustomUserAdmin)
admin_site.register(Profile, ProfileAdmin)
admin_site.register(UserBookShelf, UserBookShelfAdmin)
admin_site.register(Group)

# Seção de Gerenciamento da Home (O novo centro de tudo)
admin_site.register(HomeSection, HomeSectionAdmin)

# Seção de Itens de Conteúdo (Gerenciados individualmente)
admin_site.register(VideoItem, VideoItemAdmin)
admin_site.register(VideoSection, VideoSectionAdmin)
admin_site.register(EventItem, EventItemAdmin)

# Seção de Configurações de Conteúdo Customizado
admin_site.register(CustomSection, CustomSectionAdmin)
admin_site.register(CustomSectionType, CustomSectionTypeAdmin)
admin_site.register(CustomSectionLayout, CustomSectionLayoutAdmin)

logger.info("Módulo administrativo CG BookStore inicializado com sucesso.")

__all__ = ['admin_site']
# cgbookstore/apps/core/admin/__init__.py
"""
Módulo de inicialização para o pacote de administração do sistema.

Este arquivo importa todos os módulos de administração individuais e
registra os modelos no site de administração personalizado.
"""

import logging
from django.contrib.auth.models import Group

# Importações de modelos
from ..models import User, Profile, Book, UserBookShelf
from ..models.banner import Banner
from ..models.author import Author, AuthorSection
from ..models.home_content import (
    HomeSection, BookShelfSection,
    VideoSection, Advertisement, LinkGridItem, VideoSectionItem, VideoItem,
    DefaultShelfType, CustomSectionType, CustomSectionLayout, CustomSection,
    EventItem, BackgroundSettings
)

# Importações de componentes de administração
from .site import DatabaseAdminSite
from .user_admin import CustomUserAdmin, ProfileAdmin
from .book_admin import BookAdmin, BookCategoryAdmin
from .author_admin import AuthorAdmin, AuthorSectionAdmin
from .shelf_admin import (
    DefaultShelfTypeAdmin, UserBookShelfAdmin,
    HomeSectionAdmin, BookShelfSectionAdmin,
    BookShelfItemInline
)

from .content_admin import (
    BannerAdmin, VideoItemAdmin, VideoSectionAdmin,
    VideoItemInline, AdvertisementAdmin, BackgroundSettingsAdmin
)

from .custom_section_admin import (
    CustomSectionTypeAdmin, CustomSectionLayoutAdmin,
    CustomSectionAdmin, EventItemAdmin, EventItemInline
)

# Configuração do logger
logger = logging.getLogger(__name__)

# Criação do site administrativo personalizado
admin_site = DatabaseAdminSite(name='admin')

# Registro de todos os modelos
admin_site.register(User, CustomUserAdmin)
admin_site.register(Profile, ProfileAdmin)
admin_site.register(UserBookShelf, UserBookShelfAdmin)
admin_site.register(Banner, BannerAdmin)
admin_site.register(HomeSection, HomeSectionAdmin)
admin_site.register(BookShelfSection, BookShelfSectionAdmin)
admin_site.register(Advertisement, AdvertisementAdmin)
admin_site.register(Group)
admin_site.register(DefaultShelfType, DefaultShelfTypeAdmin)
admin_site.register(VideoItem, VideoItemAdmin)
admin_site.register(VideoSection, VideoSectionAdmin)
admin_site.register(Book, BookAdmin)
admin_site.register(Author, AuthorAdmin)
admin_site.register(AuthorSection, AuthorSectionAdmin)
admin_site.register(CustomSectionType, CustomSectionTypeAdmin)
admin_site.register(CustomSectionLayout, CustomSectionLayoutAdmin)
admin_site.register(CustomSection, CustomSectionAdmin)
admin_site.register(EventItem, EventItemAdmin)
admin_site.register(BackgroundSettings, BackgroundSettingsAdmin)

# Log de inicialização
logger.info("Módulo administrativo CG BookStore inicializado com sucesso.")

# Este é o site administrativo personalizado a ser exposto para uso
__all__ = ['admin_site']
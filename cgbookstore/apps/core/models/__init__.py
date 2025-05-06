# cgbookstore/apps/core/models/__init__.py
"""
Inicialização do pacote de modelos.

Este arquivo importa todos os modelos individuais e os expõe
para uso em outros módulos do projeto.
"""
from .profile import Profile, Achievement, UserAchievement, ReadingStats
# Importações de usuário e perfil
from .user import User
from .author import Author

# Importações de livro e prateleira
from .book import Book, UserBookShelf, BookAuthor

# Importações de conteúdo da home
from .home_content import (
    HomeSection, BookShelfSection, BookShelfItem,
    VideoSection, VideoItem, VideoSectionItem,
    Advertisement, LinkGridItem,
    DefaultShelfType,
    CustomSectionType, CustomSectionLayout, CustomSection,
    EventItem, BackgroundSettings
)

# Importações de banner
from .banner import Banner


# Lista de modelos disponíveis para importação
__all__ = [
    'User', 'Profile',
    'Achievement', 'UserAchievement', 'ReadingStats',
    'Book', 'UserBookShelf', 'BookAuthor',
    'HomeSection', 'BookShelfSection', 'BookShelfItem',
    'VideoSection', 'VideoItem', 'VideoSectionItem',
    'Advertisement', 'LinkGridItem',
    'DefaultShelfType',
    'CustomSectionType', 'CustomSectionLayout', 'CustomSection',
    'EventItem', 'Banner', 'BackgroundSettings', 'Author',
]
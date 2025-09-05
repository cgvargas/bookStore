# Arquivo: cgbookstore/apps/core/models/__init__.py

# Do home_content.py
from .home_content import (
    HomeSection,
    HomeSectionBookItem,
    VideoItem,
    VideoSection,
    VideoSectionItem,
    Advertisement,
    LinkGridItem,
    CustomSectionType,
    CustomSectionLayout,
    CustomSection,
    EventItem,
    BackgroundSettings,
)

# Do book.py
from .book import Book, BookAuthor, UserBookShelf

# Do author.py
from .author import Author, AuthorSection, AuthorSectionItem

# Do banner.py
from .banner import Banner

# Do profile.py
from .profile import Profile
from .profile import ReadingProgress, ReadingStats

# Do user.py
from .user import User

# O __all__ define quais nomes são exportados publicamente.
# Garantimos que todos os modelos estejam listados aqui.
__all__ = [
    'HomeSection', 'HomeSectionBookItem', 'VideoItem', 'VideoSection',
    'VideoSectionItem', 'Advertisement', 'LinkGridItem', 'CustomSectionType',
    'CustomSectionLayout', 'CustomSection', 'EventItem', 'BackgroundSettings',
    'Book', 'BookAuthor', 'UserBookShelf', 'Author', 'AuthorSection',
    'AuthorSectionItem', 'Banner', 'Profile', 'ReadingProgress', 'ReadingStats', 'User',
]

# cgbookstore/apps/core/models/__init__.py

from .user import User
from .profile import Profile
from .book import Book, UserBookShelf
from .banner import Banner
from ..recommendations.analytics.models import RecommendationInteraction

__all__ = [
    'User',
    'Profile',
    'Book',
    'UserBookShelf',
    'Banner',
    'RecommendationInteraction'
]


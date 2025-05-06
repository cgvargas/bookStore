# cgbookstore/apps/core/managers/__init__.py

from cgbookstore.apps.core.managers.book_managers import BookManager, BookQuerySet

__all__ = ['BookManager', 'BookQuerySet']
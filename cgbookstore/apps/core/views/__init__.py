from .general import IndexView, SobreView, ContatoView, PoliticaPrivacidadeView, TermosUsoView, RegisterView
from .auth import CustomLoginView, CustomLogoutView
from .profile import ProfileUpdateView
from .book import (
    BookSearchView, search_books, add_to_shelf, remove_from_shelf,
    get_book_details, update_book, move_book, add_book_manual
)

__all__ = [
    # Views gerais
    'IndexView', 'SobreView', 'ContatoView', 'PoliticaPrivacidadeView', 'TermosUsoView',
    # Views de autenticação
    'CustomLoginView', 'CustomLogoutView', 'RegisterView',
    # Views de perfil
    'ProfileUpdateView',
    # Views de livros
    'BookSearchView', 'search_books', 'add_to_shelf', 'remove_from_shelf',
    'get_book_details', 'update_book', 'move_book', 'add_book_manual'
]
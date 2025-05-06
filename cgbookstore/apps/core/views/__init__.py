"""
Módulo de inicialização das views do aplicativo core.

Importa e exporta todas as views utilizadas no projeto,
organizadas por categorias:
- Views gerais (página inicial, sobre, contato)
- Views de autenticação
- Views de perfil
- Views de gerenciamento de livros
"""

# Importações de views gerais
from .general import (
    IndexView,       # Página inicial
    SobreView,       # Página institucional
    ContatoView,     # Formulário de contato
    PoliticaPrivacidadeView,  # Política de privacidade
    TermosUsoView,   # Termos de uso
    RegisterView     # Registro de novos usuários
)

# Importações de views de autenticação
from .auth import (
    CustomLoginView,   # Login personalizado
    CustomLogoutView   # Logout personalizado
)

# Importações de views de perfil
from .profile import (
    ProfileUpdateView  # Atualização do perfil de usuário
)

# Importações de views de livros
from .book import (
    BookSearchView,        # Busca de livros
    search_books,          # Endpoint de busca
    add_to_shelf,          # Adicionar livro à prateleira
    remove_from_shelf,     # Remover livro da prateleira
    get_book_details,      # Obter detalhes de livro
    update_book,           # Atualizar informações de livro
    move_book,             # Mover livro entre prateleiras
    add_book_manual        # Adicionar livro manualmente
)

from .book_edit import BookEditView

# Exporta todas as views para facilitar importação
__all__ = [
    # Views gerais
    'IndexView', 'SobreView', 'ContatoView', 'PoliticaPrivacidadeView', 'TermosUsoView',
    # Views de autenticação
    'CustomLoginView', 'CustomLogoutView', 'RegisterView',
    # Views de perfil
    'ProfileUpdateView',
    # Views de livros
    'BookSearchView', 'search_books', 'add_to_shelf', 'remove_from_shelf',
    'get_book_details', 'update_book', 'move_book', 'add_book_manual', 'BookEditView'
]
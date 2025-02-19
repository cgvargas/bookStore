# cgbookstore/apps/core/urls.py
"""
Configuração de URLs para o aplicativo core do CG BookStore.

Agrupa todas as rotas da aplicação, organizadas por categorias:
- Páginas principais
- Autenticação
- Perfil de usuário
- Gerenciamento de livros
- APIs de recomendação
"""

from django.urls import path, include
from .views import ProfileUpdateView, book
from .views.profile import (
    ProfileView,
    ProfileCardStyleView,
    ProfilePhotoUpdateView
)
from .views.general import (
    IndexView,
    RegisterView,
    SobreView,
    ContatoView,
    PoliticaPrivacidadeView,
    TermosUsoView
)
from .views.auth import (
    CustomLoginView,
    CustomLogoutView,
    CustomPasswordResetView,
    CustomPasswordResetDoneView,
    CustomPasswordResetConfirmView,
    CustomPasswordResetCompleteView,
    EmailVerificationView,
)
from .views.book import (
    BookSearchView,
    search_books,
    add_to_shelf,
    remove_from_shelf,
    get_book_details,
    update_book,
    move_book,
    BookDetailView,
)

# Padrões de URL para o aplicativo core
urlpatterns = [
    # Rotas de Páginas Institucionais
    # Páginas principais e informativas do site
    path('', IndexView.as_view(), name='index'),
    path('sobre/', SobreView.as_view(), name='sobre'),
    path('contato/', ContatoView.as_view(), name='contato'),
    path('politica-privacidade/', PoliticaPrivacidadeView.as_view(), name='politica_privacidade'),
    path('termos-uso/', TermosUsoView.as_view(), name='termos_uso'),

    # Rotas de Autenticação
    # Gerenciamento de login, logout, registro e reset de senha
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),

    # Rotas de Reset de Senha
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('password-reset/complete/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # Verificação de Email
    path('verify-email/<str:uidb64>/<str:token>/', EmailVerificationView.as_view(), name='verify_email'),

    # Rotas de Perfil de Usuário
    # Gerenciamento de informações e personalização do perfil
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/edit/', ProfileUpdateView.as_view(), name='profile_update'),
    path('profile/card-style/', ProfileCardStyleView.as_view(), name='card_style'),
    path('profile/update-photo/', ProfilePhotoUpdateView.as_view(), name='profile_photo_update'),

    # Rotas de Busca e Gerenciamento de Livros
    # Funcionalidades relacionadas a livros e prateleiras
    path('books/search/', search_books, name='search_books'),
    path('books/', BookSearchView.as_view(), name='book_search'),

    # Gerenciamento de Prateleira
    path('books/add-to-shelf/', add_to_shelf, name='add_to_shelf'),
    path('books/remove-from-shelf/', remove_from_shelf, name='remove_from_shelf'),

    # Detalhes e Operações de Livros
    path('books/<int:book_id>/details/', get_book_details, name='book_details'),
    path('books/<int:book_id>/update/', update_book, name='update_book'),
    path('books/<int:book_id>/move-to-shelf/', move_book, name='move_book'),
    path('books/<int:book_id>/remove-from-shelf/', remove_from_shelf, name='remove_from_shelf'),
    path('books/add-book-manual/', book.add_book_manual, name='add_book_manual'),

    # Detalhes de Livro Específico
    path('books/<int:pk>/', BookDetailView.as_view(), name='book_detail'),

    # Rotas de API
    # Inclusão de rotas de recomendações e outras APIs
    path('api/recommendations/', include('cgbookstore.apps.core.recommendations.urls')),
]
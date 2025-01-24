# cgbookstore/apps/core/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views

from .views.profile import ProfileView
from .views import ProfileUpdateView
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
    add_book_manual,
    BookDetailView,
)

# urlpatterns permanece o mesmo...

urlpatterns = [
    # Páginas principais
    path('', IndexView.as_view(), name='index'),
    path('sobre/', SobreView.as_view(), name='sobre'),
    path('contato/', ContatoView.as_view(), name='contato'),

    # Páginas legais
    path('politica-privacidade/', PoliticaPrivacidadeView.as_view(), name='politica_privacidade'),
    path('termos-uso/', TermosUsoView.as_view(), name='termos_uso'),

    # URLS de Autenticação
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('password-reset/complete/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('verify-email/<str:uidb64>/<str:token>/', EmailVerificationView.as_view(), name='verify_email'),

    # Perfil do usuário
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/edit/', ProfileUpdateView.as_view(), name='profile_update'),

    # Busca de livros (URLs existentes)
    path('books/search/', search_books, name='search_books'),
    path('books/', BookSearchView.as_view(), name='book_search'),
    path('books/add-to-shelf/', add_to_shelf, name='add_to_shelf'),
    path('books/remove-from-shelf/', remove_from_shelf, name='remove_from_shelf'),

    # Novas URLs para gerenciamento de livros
    path('books/<int:book_id>/details/', get_book_details, name='book_details'),
    path('books/<int:book_id>/update/', update_book, name='update_book'),
    path('books/move-book/', move_book, name='move_book'),
    path('books/add-manual/', add_book_manual, name='add_book_manual'),
    path('books/<int:pk>/', BookDetailView.as_view(), name='book_detail'),

]
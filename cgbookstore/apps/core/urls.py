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
from .views.book_edit import BookEditView
from .views.profile import (
    ProfileView,
    ProfileCardStyleView,
    ProfilePhotoUpdateView, CurrentReadingView, UpdateReadingProgressView, CurrentReadingsView, FavoriteQuoteView,
    DetailedStatsView,
)
from .views.general import (
    IndexView,
    RegisterView,
    SobreView,
    ContatoView,
    PoliticaPrivacidadeView,
    TermosUsoView, PlanosView,
    PremiumSignupView, ReaderRankingView,
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
    external_book_details_view,
)

from .views.general import get_external_book_details, aceitar_cookies
from .views.recommendation_views import import_external_book
from .views import book
from .views.weather import get_weather

# Padrões de URL para o aplicativo core
urlpatterns = [

    # Rotas de Páginas Institucionais
    # Páginas principais e informativas do site
    path('', IndexView.as_view(), name='index'),
    path('sobre/', SobreView.as_view(), name='sobre'),
    path('contato/', ContatoView.as_view(), name='contato'),
    path('politica-privacidade/', PoliticaPrivacidadeView.as_view(), name='politica_privacidade'),
    path('termos-uso/', TermosUsoView.as_view(), name='termos_uso'),
    path('aceitar-cookies/', aceitar_cookies, name='aceitar_cookies'),
    path('planos/', PlanosView.as_view(), name='planos'),
    path('premium-signup/', PremiumSignupView.as_view(), name='premium_signup'),
    path('checkout/premium/', book.CheckoutPremiumView.as_view(), name='checkout_premium'),

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
    path('profile/card-theme/', ProfileCardStyleView.as_view(), name='card_theme'),
    path('profile/update-photo/', ProfilePhotoUpdateView.as_view(), name='profile_photo_update'),
    path('profile/current-reading/', CurrentReadingView.as_view(), name='current_reading'),
    path('profile/update-reading-progress/', UpdateReadingProgressView.as_view(), name='update_reading_progress'),
    path('profile/lendo/', CurrentReadingsView.as_view(), name='current_readings'),
    path('profile/favorite-quote/', FavoriteQuoteView.as_view(), name='profile_favorite_quote'),
    path('profile/detailed-stats/', DetailedStatsView.as_view(), name='detailed_stats'),

    # Rotas de Busca e Gerenciamento de Livros
    # Funcionalidades relacionadas a livros e prateleiras
    path('books/search/', search_books, name='search_books'),
    path('books/', BookSearchView.as_view(), name='book_search'),

    # Gerenciamento de Prateleira
    path('books/add-to-shelf/', add_to_shelf, name='add_to_shelf'),
    path('books/remove-from-shelf/', remove_from_shelf, name='remove_from_shelf'),

    # Rotas para importação de livros externos
    path('books/import-external/', import_external_book, name='import_external_book'),
    path('books/add-external-to-shelf/', book.add_external_to_shelf, name='add_external_to_shelf'),

    # Rota para detalhes de livros externos
    path('books/external/<str:external_id>/details/', external_book_details_view, name='external_book_details'),

    # Detalhes e Operações de Livros
    path('books/<int:book_id>/details/', get_book_details, name='book_details_api'),

    # Renomeado para clarificar que é uma API
    path('books/<int:book_id>/update/', update_book, name='update_book'),
    path('books/<int:book_id>/move-to-shelf/', move_book, name='move_book'),
    path('books/move-book/', move_book, name='move_book_json'),
    path('books/<int:book_id>/remove-from-shelf/', remove_from_shelf, name='remove_from_shelf'),
    path('books/add-book-manual/', book.add_book_manual, name='add_book_manual'),

    # Detalhes de Livro Específico - Esta é a rota que deve ser usada para visualização de detalhes
    path('books/<int:pk>/', BookDetailView.as_view(), name='book_detail'),
    path('books/<int:pk>/edit/', BookEditView.as_view(), name='book_edit'),

    # Rotas para as páginas de categorias de livros
    path('catalogue/', book.CatalogueView.as_view(), name='catalogue'),
    path('new-releases/', book.NewReleasesView.as_view(), name='new_releases'),
    path('bestsellers/', book.BestSellersView.as_view(), name='bestsellers'),
    path('recommended/', book.RecommendedBooksView.as_view(), name='recommended_books'),

    # Rotas de API
    # Inclusão de rotas de recomendações e outras APIs
    path('api/recommendations/', include('cgbookstore.apps.core.recommendations.urls')),
    path('api/recommendations/book/<str:external_id>/', get_external_book_details, name='external_book_details'),
    path('api/weather/', get_weather, name='weather_api'),

    # Página de Ranking de Leitores
    path('ranking-leitores/', ReaderRankingView.as_view(), name='ranking_leitores'),

]
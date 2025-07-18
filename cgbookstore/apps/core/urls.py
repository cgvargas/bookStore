# cgbookstore/apps/core/urls.py
"""
Configuração de URLs para o aplicativo core do CG BookStore.
"""

from django.urls import path, include
from .views import ProfileUpdateView, book, image_proxy
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
    get_external_book_details, aceitar_cookies
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
from .views.recommendation_views import import_external_book
from .views.weather import get_weather

app_name = 'core'

# Padrões de URL para o aplicativo core
urlpatterns = [

    # Rotas de Páginas Institucionais
    path('', IndexView.as_view(), name='index'), # <-- A URL 'index' está aqui!
    path('sobre/', SobreView.as_view(), name='sobre'),
    path('contato/', ContatoView.as_view(), name='contato'),
    path('politica-privacidade/', PoliticaPrivacidadeView.as_view(), name='politica_privacidade'),
    path('termos-uso/', TermosUsoView.as_view(), name='termos_uso'),
    path('aceitar-cookies/', aceitar_cookies, name='aceitar_cookies'),
    path('planos/', PlanosView.as_view(), name='planos'),
    path('premium-signup/', PremiumSignupView.as_view(), name='premium_signup'),
    path('checkout/premium/', book.CheckoutPremiumView.as_view(), name='checkout_premium'),

    # Rotas de Autenticação
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
    path('books/search/', search_books, name='search_books'),
    path('books/', BookSearchView.as_view(), name='book_search'),
    path('books/add-to-shelf/', add_to_shelf, name='add_to_shelf'),
    path('books/remove-from-shelf/', remove_from_shelf, name='remove_from_shelf'),
    path('books/import-external/', import_external_book, name='import_external_book'),
    path('books/add-external-to-shelf/', book.add_external_to_shelf, name='add_external_to_shelf'),
    path('books/external/<str:external_id>/details/', external_book_details_view, name='external_book_details'),
    path('books/<int:book_id>/details/', get_book_details, name='book_details_api'),
    path('books/<int:book_id>/update/', update_book, name='update_book'),
    path('books/<int:book_id>/move-to-shelf/', move_book, name='move_book'),
    path('books/move-book/', move_book, name='move_book_json'),
    path('books/<int:book_id>/remove-from-shelf/', remove_from_shelf, name='remove_from_shelf'),
    path('books/add-book-manual/', book.add_book_manual, name='add_book_manual'),
    path('books/<int:pk>/', BookDetailView.as_view(), name='book_detail'),
    path('books/<int:pk>/edit/', BookEditView.as_view(), name='book_edit'),

    # Rotas para as páginas de categorias de livros
    path('catalogue/', book.CatalogueView.as_view(), name='catalogue'),
    path('new-releases/', book.NewReleasesView.as_view(), name='new_releases'),
    path('bestsellers/', book.BestSellersView.as_view(), name='bestsellers'),
    path('recommended/', book.RecommendedBooksView.as_view(), name='recommended_books'),

    path('api/weather/', get_weather, name='weather_api'),
    path('image-proxy/', image_proxy.google_books_image_proxy, name='image_proxy'),
    path('ranking-leitores/', ReaderRankingView.as_view(), name='ranking_leitores'),

    # Rotas de Autores - Incluindo o namespace 'authors'
    path('authors/', include(('cgbookstore.apps.core.urls_author', 'authors'))),
]
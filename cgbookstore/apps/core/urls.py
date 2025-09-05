# Arquivo: cgbookstore/apps/core/urls.py

from django.urls import path, include
from .views import book, image_proxy
from .views.book_edit import BookEditView
from .views.profile import (
    ProfileView, ProfileUpdateView, ProfileCardStyleView,
    ProfilePhotoUpdateView, FavoriteQuoteView, ProfileReadingStatusView,
    UpdateReadingProgressView, SetCurrentReadingView,
    get_detailed_stats, get_current_reading_status,
    get_user_achievements
)
from .views.general import (
    IndexView, RegisterView, SobreView, ContatoView, PoliticaPrivacidadeView,
    TermosUsoView, PlanosView, PremiumSignupView, ReaderRankingView,
    get_external_book_details, aceitar_cookies,
    EventosView, get_csrf_token
)
from .views.auth import (
    CustomLoginView, CustomLogoutView, CustomPasswordResetView,
    CustomPasswordResetDoneView, CustomPasswordResetConfirmView,
    CustomPasswordResetCompleteView, EmailVerificationView
)
from .views.book import (
    BookSearchView,
    search_books,
    add_to_shelf,
    add_external_book_to_shelf,
    remove_from_shelf,
    get_book_details,
    update_book,
    move_book,
    BookDetailView,
    external_book_details_view,
    CatalogueView,
    NewReleasesView,
    BestSellersView,
    RecommendedBooksView,
    CheckoutPremiumView,
    add_book_manual
)
from .views.recommendation_views import import_external_book

app_name = 'core'

urlpatterns = [
    # Rotas de Páginas Institucionais
    path('', IndexView.as_view(), name='index'),
    path('sobre/', SobreView.as_view(), name='sobre'),
    path('contato/', ContatoView.as_view(), name='contato'),
    path('politica-privacidade/', PoliticaPrivacidadeView.as_view(), name='politica_privacidade'),
    path('termos-uso/', TermosUsoView.as_view(), name='termos_uso'),
    path('aceitar-cookies/', aceitar_cookies, name='aceitar_cookies'),
    path('planos/', PlanosView.as_view(), name='planos'),
    path('premium-signup/', PremiumSignupView.as_view(), name='premium_signup'),
    path('checkout/premium/', CheckoutPremiumView.as_view(), name='checkout_premium'),

    # === 2. ADICIONAMOS A NOVA ROTA PARA A PÁGINA DE EVENTOS ===
    path('eventos/', EventosView.as_view(), name='eventos'),

    # Rotas de Autenticação
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('csrf-token/', get_csrf_token, name='csrf_token'),

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
    path('profile/favorite-quote/', FavoriteQuoteView.as_view(), name='profile_favorite_quote'),
    path('profile/detailed-stats/', get_detailed_stats, name='get_detailed_stats'),
    path('profile/current-reading/', get_current_reading_status, name='get_current_reading_status'),
    path('profile/api/achievements/', get_user_achievements, name='get_user_achievements'),

    # Rotas de Status de Leitura
    path('profile/lendo/', ProfileReadingStatusView.as_view(), {'status': 'lendo'}, name='profile_lendo'),
    path('profile/lidos/', ProfileReadingStatusView.as_view(), {'status': 'lido'}, name='profile_lidos'),
    path('profile/vou-ler/', ProfileReadingStatusView.as_view(), {'status': 'vou_ler'}, name='profile_vou_ler'),
    path('profile/favoritos/', ProfileReadingStatusView.as_view(), {'status': 'favorito'}, name='profile_favoritos'),
    path('profile/abandonados/', ProfileReadingStatusView.as_view(), {'status': 'abandonado'},
         name='profile_abandonados'),
    path('profile/update-reading-progress/', UpdateReadingProgressView.as_view(), name='update_reading_progress'),
    path('profile/set-current-reading/', SetCurrentReadingView.as_view(), name='set_current_reading'),

    # Rotas de Busca e Gerenciamento de Livros
    path('books/search/', search_books, name='search_books'),
    path('books/', BookSearchView.as_view(), name='book_search'),
    path('books/add-to-shelf/', add_to_shelf, name='add_to_shelf'),
    path('books/add-external-to-shelf/', add_external_book_to_shelf, name='add_external_to_shelf'),
    path('books/<int:book_id>/remove-from-shelf/', remove_from_shelf, name='remove_from_shelf'),
    path('books/import-external/', import_external_book, name='import_external_book'),
    path('books/external/<str:external_id>/details/', external_book_details_view, name='external_book_details'),
    path('books/<int:book_id>/details/', get_book_details, name='book_details_api'),
    path('books/<int:book_id>/update/', update_book, name='update_book'),
    path('books/<int:book_id>/move/', move_book, name='move_book'),
    path('books/add-book-manual/', add_book_manual, name='add_book_manual'),
    path('books/<int:pk>/', BookDetailView.as_view(), name='book_detail'),
    path('books/<int:pk>/edit/', BookEditView.as_view(), name='book_edit'),

    # Rotas para as páginas de categorias de livros
    path('catalogue/', CatalogueView.as_view(), name='catalogue'),
    path('new-releases/', NewReleasesView.as_view(), name='new_releases'),
    path('bestsellers/', BestSellersView.as_view(), name='bestsellers'),
    path('recommended/', RecommendedBooksView.as_view(), name='recommended_books'),

    path('image-proxy/', image_proxy.google_books_image_proxy, name='image_proxy'),
    path('ranking-leitores/', ReaderRankingView.as_view(), name='ranking_leitores'),

    # Rotas de Autores
    path('authors/', include(('cgbookstore.apps.core.urls_author', 'authors'))),
]
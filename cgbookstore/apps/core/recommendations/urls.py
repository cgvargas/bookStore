# cgbookstore/apps/core/recommendations/urls.py
"""
Configuração de URLs para o sistema de recomendações.
Inclui rotas para recomendações tradicionais e integração com API externa.
"""

from django.urls import path
from .api import endpoints
from cgbookstore.apps.core.views.recommendation_views import (
    get_recommendations_view,
    get_personalized_shelf_view,
    get_recommendations_json,
    get_external_book_details,
    import_external_book,
    add_external_book_to_shelf
)

app_name = 'recommendations-api'

urlpatterns = [
    path('mixed/', get_recommendations_view, name='mixed_recommendations'),
    path('shelf/', get_personalized_shelf_view, name='personalized_shelf'),
    path('json/', get_recommendations_json, name='recommendations_api'),
    path('book/<str:external_id>/', get_external_book_details, name='external_book_details'),
    path('import-book/', import_external_book, name='import_external_book'),
    path('add-external-book/', add_external_book_to_shelf, name='add_external_book'),
]
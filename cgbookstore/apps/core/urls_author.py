"""
URLs para as views relacionadas a autores.

Este arquivo define as rotas para as views de listagem,
detalhes e outras funcionalidades relacionadas a autores.
"""

from django.urls import path
from .views.author_views import AuthorListView, AuthorDetailView, AuthorSectionView

app_name = 'authors'

urlpatterns = [
    # Lista de autores
    path('', AuthorListView.as_view(), name='author-list'),

    # Detalhes de um autor específico
    path('<slug:slug>/', AuthorDetailView.as_view(), name='author-detail'),
    path('section/<int:section_id>/', AuthorSectionView.as_view(), name='author-section'),
]
# cgbookstore/apps/core/recommendations/api/urls.py

from django.urls import path
from . import endpoints

app_name = 'recommendations'  # Alterado para corresponder ao namespace

urlpatterns = [
    path('', endpoints.get_recommendations, name='recommendations'),
    path('personalized-shelf/', endpoints.get_personalized_shelf, name='personalized-shelf'),
]
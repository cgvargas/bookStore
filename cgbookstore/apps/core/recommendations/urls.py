from django.urls import path
from .api import endpoints

app_name = 'recommendations-api'

urlpatterns = [
    # Endpoints de recomendações
    path('', endpoints.get_recommendations, name='recommendations'),
    path('shelf/', endpoints.get_personalized_shelf, name='personalized-shelf'),
]
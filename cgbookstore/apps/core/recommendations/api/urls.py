from django.urls import path, include
from . import endpoints

app_name = 'recommendations'

urlpatterns = [
    # Endpoints de recomendações
    path('', endpoints.get_recommendations, name='recommendations'),
    path('shelf/', endpoints.get_personalized_shelf, name='personalized_shelf'),
]
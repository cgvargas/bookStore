from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from ..engine import RecommendationEngine
from ..utils.cache_manager import RecommendationCache
from .serializers import BookRecommendationSerializer, PersonalizedShelfSerializer

User = get_user_model()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recommendations(request):
    """Endpoint para obter recomendações gerais"""
    limit = request.query_params.get('limit', 10)
    try:
        limit = int(limit)
    except ValueError:
        limit = 10

    # Tenta obter do cache
    cached_recommendations = RecommendationCache.get_recommendations(request.user)
    if cached_recommendations:
        return Response(cached_recommendations[:limit])

    # Se não estiver em cache, gera novas recomendações
    engine = RecommendationEngine()
    recommended_books = engine.get_recommendations(request.user, limit=limit)

    # Serializa os dados
    serializer = BookRecommendationSerializer(recommended_books, many=True)

    # Salva no cache
    RecommendationCache.set_recommendations(request.user, serializer.data)

    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_personalized_shelf(request):
    """Endpoint para obter prateleira personalizada"""
    shelf_size = request.query_params.get('shelf_size', 5)
    try:
        shelf_size = int(shelf_size)
    except ValueError:
        shelf_size = 5

    # Tenta obter do cache
    cached_shelf = RecommendationCache.get_shelf(request.user)
    if cached_shelf:
        # Ajusta o tamanho das listas conforme solicitado
        for key in cached_shelf:
            cached_shelf[key] = cached_shelf[key][:shelf_size]
        return Response(cached_shelf)

    # Se não estiver em cache, gera nova prateleira
    engine = RecommendationEngine()
    shelf_data = engine.get_personalized_shelf(request.user, shelf_size=shelf_size)

    # Serializa os dados
    serializer = PersonalizedShelfSerializer(shelf_data)

    # Salva no cache
    RecommendationCache.set_shelf(request.user, serializer.data)

    return Response(serializer.data)
import time
from django.db import connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from ..engine import RecommendationEngine


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_performance_metrics(request):
    """Endpoint para medir performance do sistema de recomendações"""
    engine = RecommendationEngine()
    metrics = {}

    # Mede tempo de resposta
    start_time = time.time()
    recommendations = engine.get_recommendations(request.user)
    end_time = time.time()
    metrics['response_time'] = end_time - start_time

    # Mede queries executadas
    initial_queries = len(connection.queries)
    _ = list(recommendations)  # Força execução das queries
    final_queries = len(connection.queries)
    metrics['total_queries'] = final_queries - initial_queries

    # Coleta estatísticas
    metrics['total_recommendations'] = len(recommendations)
    metrics['cache_stats'] = engine.get_cache_stats()

    return Response(metrics)
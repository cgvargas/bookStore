from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .tracker import AnalyticsTracker
from .serializers import InteractionSerializer, InteractionStatsSerializer

User = get_user_model()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def track_interaction(request):
    """Endpoint para registrar uma interação com recomendação"""
    serializer = InteractionSerializer(data=request.data)

    if serializer.is_valid():
        AnalyticsTracker.track_interaction(
            user_id=request.user.id,
            book_id=serializer.validated_data['book_id'],
            interaction_type=serializer.validated_data['interaction_type'],
            source=serializer.validated_data['source'],
            score=serializer.validated_data.get('score'),
            position=serializer.validated_data.get('position'),
            metadata=serializer.validated_data.get('metadata', {})
        )
        return Response({'status': 'success'}, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_stats(request):
    """Endpoint para obter estatísticas do usuário"""
    stats = AnalyticsTracker.get_user_interaction_stats(request.user.id)
    serializer = InteractionStatsSerializer(stats)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_global_stats(request):
    """Endpoint para obter estatísticas globais (apenas admin)"""
    from django.db.models import Count
    from .models import RecommendationInteraction

    global_stats = {
        'total_interactions': RecommendationInteraction.objects.count(),
        'interactions_by_type': dict(
            RecommendationInteraction.objects.values('interaction_type')
            .annotate(count=Count('id'))
            .values_list('interaction_type', 'count')
        ),
        'interactions_by_source': dict(
            RecommendationInteraction.objects.values('source')
            .annotate(count=Count('id'))
            .values_list('source', 'count')
        ),
        'active_users': RecommendationInteraction.objects.values('user') \
            .distinct().count()
    }

    return Response(global_stats)
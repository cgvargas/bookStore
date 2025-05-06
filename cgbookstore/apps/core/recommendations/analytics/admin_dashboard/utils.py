# Arquivo: cgbookstore/apps/core/recommendations/analytics/admin_dashboard/utils.py
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Count, Avg, F, Q, ExpressionWrapper, Window, Min, Max
from django.db.models.functions import ExtractWeekDay, ExtractHour, Lead
from django.forms import DurationField
from django.utils import timezone
from datetime import timedelta
from django.db import models  # Adicionado para resolver o Q

from cgbookstore.apps.core.recommendations.analytics.models import RecommendationInteraction


def get_date_range_metrics(queryset, start_date=None, end_date=None):
    """
    Obtém métricas para um intervalo de datas específico
    """
    if not start_date:
        start_date = timezone.now() - timedelta(days=30)
    if not end_date:
        end_date = timezone.now()

    return queryset.filter(
        timestamp__gte=start_date,
        timestamp__lte=end_date
    )


def calculate_effectiveness_rate(interactions):
    """
    Calcula a taxa de efetividade das recomendações
    """
    total = interactions.count()
    if total == 0:
        return 0

    successful = interactions.filter(successful=True).count()
    return (successful / total) * 100


def format_chart_data(data_queryset):
    """
    Formata dados para uso em gráficos
    """
    return {
        'labels': [str(item['date']) for item in data_queryset],
        'values': [item['count'] for item in data_queryset]
    }


def calculate_conversion_rates(interactions, start_date=None, end_date=None):
    """
    Calcula taxas de conversão das recomendações por fonte
    """
    filtered_interactions = get_date_range_metrics(interactions, start_date, end_date)

    conversion_rates = {}
    for source, _ in RecommendationInteraction.SOURCE_TYPES:
        source_interactions = filtered_interactions.filter(source=source)
        total = source_interactions.count()

        if total > 0:
            conversions = source_interactions.filter(
                interaction_type__in=['add_shelf', 'purchase']
            ).count()
            rate = (conversions / total) * 100
            conversion_rates[source] = {
                'total': total,
                'conversions': conversions,
                'rate': round(rate, 2)
            }

    return conversion_rates


def get_conversion_trend(interactions, days=30):
    """
    Calcula tendência de conversão comparando com período anterior
    """
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    previous_start = start_date - timedelta(days=days)

    current_rates = calculate_conversion_rates(interactions, start_date, end_date)
    previous_rates = calculate_conversion_rates(interactions, previous_start, start_date)

    trends = {}
    for source in current_rates:
        if source in previous_rates and previous_rates[source]['rate'] > 0:
            change = ((current_rates[source]['rate'] - previous_rates[source]['rate'])
                      / previous_rates[source]['rate'] * 100)
            trends[source] = round(change, 2)
        else:
            trends[source] = 0

    return trends


def get_popular_books_metrics(interactions, start_date=None, end_date=None, limit=10):
    """
    Análise de popularidade dos livros baseada em interações
    """
    filtered = get_date_range_metrics(interactions, start_date, end_date)

    popular_books = filtered.values(
        'book__id',
        'book__titulo'
    ).annotate(
        views=Count('id', filter=models.Q(interaction_type='view')),
        clicks=Count('id', filter=models.Q(interaction_type='click')),
        adds=Count('id', filter=models.Q(interaction_type='add_shelf')),
        purchases=Count('id', filter=models.Q(interaction_type='purchase'))
    ).annotate(
        engagement_score=(
                models.F('views') * 1 +
                models.F('clicks') * 2 +
                models.F('adds') * 3 +
                models.F('purchases') * 4
        )
    ).order_by('-engagement_score')[:limit]

    return list(popular_books)


def get_popularity_trend(book_id, interactions, days=30):
    """
    Calcula tendência de popularidade de um livro
    """
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    previous_start = start_date - timedelta(days=days)

    current_score = get_book_engagement_score(interactions, book_id, start_date, end_date)
    previous_score = get_book_engagement_score(interactions, book_id, previous_start, start_date)

    if previous_score > 0:
        return ((current_score - previous_score) / previous_score) * 100
    return 0


def get_book_engagement_score(interactions, book_id, start_date, end_date):
    """
    Calcula score de engajamento para um livro específico
    """
    metrics = get_date_range_metrics(
        interactions.filter(book_id=book_id),
        start_date,
        end_date
    ).aggregate(
        views=Count('id', filter=models.Q(interaction_type='view')),
        clicks=Count('id', filter=models.Q(interaction_type='click')),
        adds=Count('id', filter=models.Q(interaction_type='add_shelf')),
        purchases=Count('id', filter=models.Q(interaction_type='purchase'))
    )

    return (
            metrics['views'] * 1 +
            metrics['clicks'] * 2 +
            metrics['adds'] * 3 +
            metrics['purchases'] * 4
    )


def get_category_metrics(interactions, start_date=None, end_date=None, limit=10):
    """
    Análise de métricas por categoria
    """
    filtered = get_date_range_metrics(interactions, start_date, end_date)

    return filtered.values(
        'book__categoria'  # Alterado de 'book__categoria__nome' para 'book__categoria'
    ).annotate(
        total_interactions=Count('id'),
        views=Count('id', filter=Q(interaction_type='view')),
        clicks=Count('id', filter=Q(interaction_type='click')),
        adds=Count('id', filter=Q(interaction_type='add_shelf')),
        purchases=Count('id', filter=Q(interaction_type='purchase'))
    ).annotate(
        conversion_rate=ExpressionWrapper(
            (F('purchases') * 100.0) / F('total_interactions'),
            output_field=models.FloatField()
        )
    ).filter(
        book__categoria__isnull=False
    ).order_by('-total_interactions')[:limit]


def get_category_trends(interactions, days=30):
    """
    Calcula tendências por categoria
    """
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    previous_start = start_date - timedelta(days=days)

    current_metrics = get_category_metrics(interactions, start_date, end_date)
    previous_metrics = get_category_metrics(interactions, previous_start, start_date)

    trends = {}
    for curr in current_metrics:
        category = curr['book__categoria__nome']
        prev = next((p for p in previous_metrics if p['book__categoria__nome'] == category), None)

        if prev and prev['total_interactions'] > 0:
            change = ((curr['total_interactions'] - prev['total_interactions'])
                      / prev['total_interactions'] * 100)
            trends[category] = round(change, 2)
        else:
            trends[category] = 0

    return trends


# Arquivo: cgbookstore/apps/core/recommendations/analytics/admin_dashboard/utils.py

def get_user_behavior_patterns(interactions, start_date=None, end_date=None):
    """
    Análise de padrões de comportamento dos usuários
    """
    filtered = get_date_range_metrics(interactions, start_date, end_date)

    # Padrões por horário
    hourly_patterns = filtered.annotate(
        hour=ExtractHour('timestamp')
    ).values('hour').annotate(
        count=Count('id')
    ).order_by('hour')

    # Padrões por dia da semana
    weekly_patterns = filtered.annotate(
        weekday=ExtractWeekDay('timestamp')
    ).values('weekday').annotate(
        count=Count('id')
    ).order_by('weekday')

    # Sequência de interações
    interaction_sequences = filtered.values(
        'user_id'
    ).annotate(
        session_interactions=ArrayAgg(
            'interaction_type',
            ordering='timestamp'
        )
    )

    # Análise de sessões
    session_metrics = analyze_user_sessions(filtered)

    return {
        'hourly_patterns': list(hourly_patterns),
        'weekly_patterns': list(weekly_patterns),
        'session_metrics': session_metrics
    }


def analyze_user_sessions(interactions, session_timeout=30):
    """
    Analisa métricas de sessão dos usuários
    """
    session_data = interactions.values(
        'user_id', 'timestamp'
    ).order_by('user_id', 'timestamp')

    sessions = []
    current_session = {'user': None, 'start': None, 'interactions': 0}

    for interaction in session_data:
        if (current_session['user'] != interaction['user_id'] or
                (interaction['timestamp'] - current_session['last_activity']).total_seconds() > session_timeout * 60):
            if current_session['user'] is not None:
                sessions.append(current_session)
            current_session = {
                'user': interaction['user_id'],
                'start': interaction['timestamp'],
                'last_activity': interaction['timestamp'],
                'interactions': 1
            }
        else:
            current_session['interactions'] += 1
            current_session['last_activity'] = interaction['timestamp']

    if current_session['user'] is not None:
        sessions.append(current_session)

    return {
        'average_session_length': sum(s['interactions'] for s in sessions) / len(sessions) if sessions else 0,
        'total_sessions': len(sessions),
        'users_with_multiple_sessions': len(set(s['user'] for s in sessions if s['interactions'] > 1))
    }


def get_engagement_kpis(interactions, start_date=None, end_date=None):
    """
    Calcula KPIs de engajamento
    """
    filtered = get_date_range_metrics(interactions, start_date, end_date)

    # KPIs gerais
    total_users = filtered.values('user_id').distinct().count()

    # Cálculos básicos da agregação
    basic_metrics = filtered.aggregate(
        total_interactions=Count('id'),
        unique_users=Count('user_id', distinct=True),
        unique_books=Count('book_id', distinct=True)
    )

    # Adiciona a média de interações por usuário manualmente para evitar divisão por zero
    engagement_metrics = basic_metrics.copy()
    if basic_metrics['unique_users'] > 0:
        engagement_metrics['avg_interactions_per_user'] = basic_metrics['total_interactions'] * 1.0 / basic_metrics[
            'unique_users']
    else:
        engagement_metrics['avg_interactions_per_user'] = 0

    kpis = {
        'engagement_metrics': engagement_metrics,

        # Taxa de retorno (usuários com mais de uma sessão)
        'return_rate': filtered.values('user_id').annotate(
            sessions=Count('timestamp__date', distinct=True)
        ).filter(sessions__gt=1).count() * 100.0 / total_users if total_users > 0 else 0,

        # Profundidade de engajamento
        'depth_metrics': filtered.values('user_id').annotate(
            interaction_depth=Count('id')
        ).aggregate(
            light_users=Count('user_id', filter=Q(interaction_depth__lte=5)),
            medium_users=Count('user_id', filter=Q(interaction_depth__gt=5, interaction_depth__lte=15)),
            heavy_users=Count('user_id', filter=Q(interaction_depth__gt=15))
        ),

        # Tempo médio entre interações (simplificado)
        'avg_time_between': None  # Removido temporariamente devido a limitações do SQLite
    }

    return kpis


def calculate_engagement_trends(interactions, days=30):
    """
    Calcula tendências dos KPIs de engajamento
    """
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    previous_start = start_date - timedelta(days=days)

    current_kpis = get_engagement_kpis(interactions, start_date, end_date)
    previous_kpis = get_engagement_kpis(interactions, previous_start, start_date)

    trends = {}

    # Calcula tendências para métricas principais
    for metric in ['total_interactions', 'unique_users', 'unique_books']:
        current = current_kpis['engagement_metrics'][metric]
        previous = previous_kpis['engagement_metrics'][metric]

        if previous > 0:
            trends[metric] = ((current - previous) / previous) * 100
        else:
            trends[metric] = 0

    # Tendência da taxa de retorno
    if previous_kpis['return_rate'] > 0:
        trends['return_rate'] = ((current_kpis['return_rate'] - previous_kpis['return_rate'])
                                 / previous_kpis['return_rate']) * 100
    else:
        trends['return_rate'] = 0

    return trends
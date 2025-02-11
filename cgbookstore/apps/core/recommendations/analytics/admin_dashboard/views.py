import calendar
import locale

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from django.db.models.functions import TruncDate
import json

from ..models import RecommendationInteraction
from .utils import (
    get_popular_books_metrics,
    get_category_metrics,
    get_user_behavior_patterns,
    get_engagement_kpis,
    calculate_engagement_trends, calculate_conversion_rates, get_conversion_trend, get_popularity_trend,
    get_category_trends
)
from ..tracker import AnalyticsTracker


@staff_member_required
def admin_dashboard(request):
    # Período padrão - últimos 30 dias
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)

    # Obter métricas gerais
    interactions = RecommendationInteraction.objects.filter(timestamp__range=[start_date, end_date])

    # Total de interações e usuários
    total_interactions = interactions.count()
    unique_users = interactions.values('user').distinct().count()
    unique_books = interactions.values('book').distinct().count()

    # Taxa de conversão
    total_purchases = interactions.filter(interaction_type='purchase').count()
    conversion_rate = (total_purchases / total_interactions * 100) if total_interactions > 0 else 0

    # Média de interações por usuário
    avg_interactions_per_user = total_interactions / unique_users if unique_users > 0 else 0

    # Taxa de retorno
    users_with_multiple = interactions.values('user').annotate(
        total=Count('id')
    ).filter(total__gt=1).count()
    return_rate = (users_with_multiple / unique_users * 100) if unique_users > 0 else 0

    # Interações diárias para o gráfico
    daily_interactions = interactions.annotate(
        date=TruncDate('timestamp')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')

    # Preparar dados para o gráfico de interações diárias
    interaction_data = {
        'labels': json.dumps([d['date'].strftime('%d/%m') for d in daily_interactions]),
        'values': json.dumps([d['count'] for d in daily_interactions])
    }

    # Obter padrões de comportamento
    behavior_patterns = get_user_behavior_patterns(interactions)
    hourly_patterns = behavior_patterns['hourly_patterns']
    weekly_patterns = behavior_patterns['weekly_patterns']
    session_metrics = behavior_patterns['session_metrics']

    # Processar padrões por período do dia
    def get_period(hour):
        if 0 <= hour <= 5:
            return 'Madrugada'
        elif 6 <= hour <= 11:
            return 'Manhã'
        elif 12 <= hour <= 17:
            return 'Tarde'
        else:
            return 'Noite'

    # Processar padrões de hora com intensidade
    hourly_patterns_grouped = {}
    if hourly_patterns:
        max_count = max(pattern['count'] for pattern in hourly_patterns)

        for pattern in hourly_patterns:
            hour = pattern['hour']
            count = pattern['count']
            intensity = (count / max_count * 100) if max_count > 0 else 0

            intensity_level = 'low'
            if intensity > 75:
                intensity_level = 'very-high'
            elif intensity > 50:
                intensity_level = 'high'
            elif intensity > 25:
                intensity_level = 'medium'

            processed_pattern = {
                'hour': hour,
                'count': count,
                'intensity': intensity_level
            }
            period = get_period(hour)
            if period not in hourly_patterns_grouped:
                hourly_patterns_grouped[period] = []
            hourly_patterns_grouped[period].append(processed_pattern)

    # Preparar dados para o gráfico semanal
    def get_weekday_name(weekday_number):
        try:
            # Tenta definir a localização para português do Brasil
            try:
                locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
            except locale.Error:
                # Fallback para configuração padrão se pt_BR não estiver disponível
                locale.setlocale(locale.LC_TIME, '')

            # Converte o número para um inteiro
            weekday_number = int(weekday_number)

            # Obtém o nome do dia da semana
            # calendar.day_name usa domingo como 0, então ajustamos
            dias = list(calendar.day_name)
            dias = dias[1:] + [dias[0]]  # Move domingo para o final

            return dias[weekday_number].capitalize()
        except (ValueError, IndexError):
            # Retorna o valor original se a conversão falhar
            return str(weekday_number)

    weekly_data = {
        'labels': [get_weekday_name(pattern['weekday']) for pattern in weekly_patterns],
        'values': [pattern['count'] for pattern in weekly_patterns]
    }
    print("Weekly Data:", weekly_data)

    # Obter métricas de engajamento
    engagement_kpis = get_engagement_kpis(interactions)
    engagement_trends = calculate_engagement_trends(interactions)

    # Preparar métricas de usuário
    total_users = float(engagement_kpis['depth_metrics']['light_users'] +
                        engagement_kpis['depth_metrics']['medium_users'] +
                        engagement_kpis['depth_metrics']['heavy_users'])

    user_segments = engagement_kpis['depth_metrics']
    if total_users > 0:
        user_segments.update({
            'light_users_percentage': (user_segments['light_users'] / total_users) * 100,
            'medium_users_percentage': (user_segments['medium_users'] / total_users) * 100,
            'heavy_users_percentage': (user_segments['heavy_users'] / total_users) * 100
        })

    context = {
        'total_interactions': total_interactions,
        'unique_users': unique_users,
        'unique_books': unique_books,
        'conversion_rate': conversion_rate,
        'avg_interactions_per_user': avg_interactions_per_user,
        'return_rate': return_rate,
        'daily_interactions': interaction_data,
        'start_date': start_date,
        'end_date': end_date,
        'hourly_patterns_grouped': hourly_patterns_grouped,
        'hourly_patterns_json': json.dumps(list(hourly_patterns)),
        'weekly_data': json.dumps(weekly_data),
        'weekly_patterns': weekly_patterns,
        'session_metrics': session_metrics,
        'popular_books': get_popular_books_metrics(interactions),
        'category_metrics': get_category_metrics(interactions),
        'user_segments': user_segments,
        'engagement_trends': engagement_trends,
        'avg_time_between': engagement_kpis['avg_time_between']
    }

    return render(request, 'core/admin_dashboard/dashboard.html', context)


@staff_member_required
def recommendation_metrics(request):
    tracker = AnalyticsTracker()
    base_metrics = tracker.get_detailed_metrics()
    interactions = RecommendationInteraction.objects.all()

    # Métricas de conversão
    conversion_rates = calculate_conversion_rates(interactions)
    conversion_trends = get_conversion_trend(interactions)

    # Define conversion_metrics corretamente
    conversion_metrics = []
    for source, data in conversion_rates.items():
        source_display = dict(RecommendationInteraction.SOURCE_TYPES)[source]
        conversion_metrics.append({
            'title': f'Taxa de Conversão - {source_display}',
            'value': f"{data['rate']}%",
            'change': conversion_trends.get(source, 0),
            'total': data['total'],
            'conversions': data['conversions']
        })

    # Métricas de popularidade
    popular_books = get_popular_books_metrics(interactions)
    popularity_trends = {
        book['book__id']: get_popularity_trend(book['book__id'], interactions)
        for book in popular_books
    }

    books_metrics = [{
        'title': book['book__titulo'],
        'views': book['views'],
        'clicks': book['clicks'],
        'adds': book['adds'],
        'purchases': book['purchases'],
        'score': book['engagement_score'],
        'trend': popularity_trends[book['book__id']]
    } for book in popular_books]

    context = {
        'metrics': base_metrics,
        'conversion_metrics': conversion_metrics,  # Agora está definido corretamente
        'popular_books': books_metrics
    }

    # Métricas por categoria
    category_data = get_category_metrics(interactions)
    category_trends = get_category_trends(interactions)

    category_metrics = [{
        'category': data['book__categoria__nome'],
        'total': data['total_interactions'],
        'views': data['views'],
        'clicks': data['clicks'],
        'adds': data['adds'],
        'purchases': data['purchases'],
        'conversion_rate': round(data['conversion_rate'], 2),
        'trend': category_trends.get(data['book__categoria__nome'], 0)
    } for data in category_data]

    context.update({
        'category_metrics': category_metrics
    })

    # Adicionar análise de comportamento
    behavior_patterns = get_user_behavior_patterns(interactions)

    context.update({
        'hourly_patterns': behavior_patterns['hourly_patterns'],
        'weekly_patterns': behavior_patterns['weekly_patterns'],
        'session_metrics': behavior_patterns['session_metrics']
    })

    # Adicionar KPIs de engajamento
    engagement_kpis = get_engagement_kpis(interactions)
    engagement_trends = calculate_engagement_trends(interactions)

    # Processar métricas para template
    engagement_metrics = [
        {
            'title': 'Total de Interações',
            'value': engagement_kpis['engagement_metrics']['total_interactions'],
            'change': engagement_trends['total_interactions']
        },
        {
            'title': 'Usuários Únicos',
            'value': engagement_kpis['engagement_metrics']['unique_users'],
            'change': engagement_trends['unique_users']
        },
        {
            'title': 'Taxa de Retorno',
            'value': f"{engagement_kpis['return_rate']:.1f}%",
            'change': engagement_trends['return_rate']
        },
        {
            'title': 'Média de Interações/Usuário',
            'value': f"{engagement_kpis['engagement_metrics']['avg_interactions_per_user']:.1f}",
            'change': None
        }
    ]

    context.update({
        'engagement_metrics': engagement_metrics,
        'user_segments': engagement_kpis['depth_metrics'],
        'avg_time_between': engagement_kpis['avg_time_between']
    })

    return render(request, 'core/admin_dashboard/metrics.html', context)
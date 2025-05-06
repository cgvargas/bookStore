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

    # Métricas das modalidades de livros
    from cgbookstore.apps.core.models.book import Book
    from cgbookstore.apps.core.models import UserBookShelf
    from django.db.models import Sum, F, ExpressionWrapper, FloatField, When, Case, Value

    # Métricas gerais para cada modalidade
    modalities_metrics = {}

    # 1. Lançamentos
    new_releases = Book.objects.filter(e_lancamento=True)
    new_releases_count = new_releases.count()
    new_releases_views = new_releases.aggregate(total=Sum('quantidade_acessos'))['total'] or 0
    total_books = Book.objects.count()
    new_releases_percent = (new_releases_count / total_books * 100) if total_books > 0 else 0

    # Tendência - comparação com período anterior
    prev_period_start = start_date - timedelta(days=30)
    prev_period_views = interactions.filter(
        book__e_lancamento=True,
        timestamp__range=[prev_period_start, start_date]
    ).count()
    current_period_views = interactions.filter(
        book__e_lancamento=True,
        timestamp__range=[start_date, end_date]
    ).count()

    if prev_period_views > 0:
        new_releases_trend = ((current_period_views - prev_period_views) / prev_period_views * 100)
    else:
        new_releases_trend = 100 if current_period_views > 0 else 0

    # Taxa de conversão para lançamentos
    new_releases_interactions = interactions.filter(book__e_lancamento=True)
    new_releases_shelf_adds = new_releases_interactions.filter(interaction_type='add_to_shelf').count()
    new_releases_conversion_rate = (new_releases_shelf_adds / new_releases_views * 100) if new_releases_views > 0 else 0

    # Top 5 lançamentos
    top_new_releases = new_releases.annotate(
        shelf_count=Count('shelves')
    ).order_by('-quantidade_acessos')[:5]

    # 2. Mais Vendidos
    bestsellers = Book.objects.filter(quantidade_vendida__gt=0).order_by('-quantidade_vendida')
    bestsellers_count = bestsellers.count()
    bestsellers_total_sales = bestsellers.aggregate(total=Sum('quantidade_vendida'))['total'] or 0
    bestsellers_views = bestsellers.aggregate(total=Sum('quantidade_acessos'))['total'] or 0

    # Tendência para mais vendidos
    prev_period_sales = interactions.filter(
        book__quantidade_vendida__gt=0,
        timestamp__range=[prev_period_start, start_date]
    ).count()
    current_period_sales = interactions.filter(
        book__quantidade_vendida__gt=0,
        timestamp__range=[start_date, end_date]
    ).count()

    if prev_period_sales > 0:
        bestsellers_trend = ((current_period_sales - prev_period_sales) / prev_period_sales * 100)
    else:
        bestsellers_trend = 100 if current_period_sales > 0 else 0

    # Taxa de conversão para mais vendidos
    bestsellers_interactions = interactions.filter(book__quantidade_vendida__gt=0)
    bestsellers_purchases = bestsellers_interactions.filter(interaction_type='purchase').count()
    bestsellers_conversion_rate = (bestsellers_purchases / bestsellers_views * 100) if bestsellers_views > 0 else 0

    # Top 5 mais vendidos
    top_bestsellers = bestsellers.annotate(
        conversion_rate=ExpressionWrapper(
            Case(
                When(quantidade_acessos__gt=0,
                     then=F('quantidade_vendida') * 100.0 / F('quantidade_acessos')),
                default=Value(0.0)
            ),
            output_field=FloatField()
        )
    )[:5]

    # 3. Recomendados
    # Recupera livros que apareceram em recomendações
    recommended_interactions = interactions.filter(source='recommendation')
    recommended_books_ids = recommended_interactions.values_list('book', flat=True).distinct()
    recommended_count = len(recommended_books_ids)
    recommended_views = recommended_interactions.filter(interaction_type='view').count()

    # Tendência para recomendados
    prev_period_rec = interactions.filter(
        source='recommendation',
        timestamp__range=[prev_period_start, start_date]
    ).count()
    current_period_rec = interactions.filter(
        source='recommendation',
        timestamp__range=[start_date, end_date]
    ).count()

    if prev_period_rec > 0:
        recommended_trend = ((current_period_rec - prev_period_rec) / prev_period_rec * 100)
    else:
        recommended_trend = 100 if current_period_rec > 0 else 0

    # Taxa de conversão para recomendados
    recommended_actions = recommended_interactions.filter(
        interaction_type__in=['add_to_shelf', 'purchase']
    ).count()
    recommended_conversion_rate = (recommended_actions / recommended_views * 100) if recommended_views > 0 else 0

    # 4. Catálogo
    catalogue_views = interactions.filter(source='catalogue').count()
    catalogue_categories = Book.objects.values('categoria').distinct().count()

    # Tendência para catálogo
    prev_period_cat = interactions.filter(
        source='catalogue',
        timestamp__range=[prev_period_start, start_date]
    ).count()
    current_period_cat = interactions.filter(
        source='catalogue',
        timestamp__range=[start_date, end_date]
    ).count()

    if prev_period_cat > 0:
        catalogue_trend = ((current_period_cat - prev_period_cat) / prev_period_cat * 100)
    else:
        catalogue_trend = 100 if current_period_cat > 0 else 0

    # Taxa de conversão para catálogo
    catalogue_interactions = interactions.filter(source='catalogue')
    catalogue_actions = catalogue_interactions.filter(
        interaction_type__in=['add_to_shelf', 'purchase']
    ).count()
    catalogue_conversion_rate = (catalogue_actions / catalogue_views * 100) if catalogue_views > 0 else 0

    # Montar dicionário de métricas
    modalities_metrics = {
        # Lançamentos
        'new_releases_count': new_releases_count,
        'new_releases_views': new_releases_views,
        'new_releases_percent': new_releases_percent,
        'new_releases_trend': new_releases_trend,
        'new_releases_conversion_rate': new_releases_conversion_rate,
        'top_new_releases': top_new_releases,

        # Mais Vendidos
        'bestsellers_count': bestsellers_count,
        'bestsellers_total_sales': bestsellers_total_sales,
        'bestsellers_views': bestsellers_views,
        'bestsellers_trend': bestsellers_trend,
        'bestsellers_conversion_rate': bestsellers_conversion_rate,
        'top_bestsellers': top_bestsellers,

        # Recomendados
        'recommended_count': recommended_count,
        'recommended_views': recommended_views,
        'recommended_trend': recommended_trend,
        'recommended_conversion_rate': recommended_conversion_rate,

        # Catálogo
        'catalogue_count': total_books,
        'catalogue_categories': catalogue_categories,
        'catalogue_views': catalogue_views,
        'catalogue_trend': catalogue_trend,
        'catalogue_conversion_rate': catalogue_conversion_rate
    }

    # Adicionar as métricas ao contexto
    context.update({
        'modalities_metrics': modalities_metrics
    })

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

    # Métricas das modalidades de livros (versão simplificada para página de métricas)
    from cgbookstore.apps.core.models.book import Book
    from cgbookstore.apps.core.models import UserBookShelf
    from django.db.models import Sum, F, ExpressionWrapper, FloatField, When, Case, Value

    # Estatísticas básicas para modalidades
    modalities_metrics = {}

    # Lançamentos
    new_releases_count = Book.objects.filter(e_lancamento=True).count()
    total_books = Book.objects.count()
    new_releases_percent = (new_releases_count / total_books * 100) if total_books > 0 else 0

    # Mais Vendidos
    bestsellers_count = Book.objects.filter(quantidade_vendida__gt=0).count()
    bestsellers_total_sales = Book.objects.filter(quantidade_vendida__gt=0).aggregate(
        total=Sum('quantidade_vendida')
    )['total'] or 0

    # Recomendados
    recommended_interactions = interactions.filter(source='recommendation')
    recommended_count = recommended_interactions.values('book').distinct().count()

    # Taxa de conversão simplificada
    recommendation_views = recommended_interactions.filter(interaction_type='view').count()
    recommendation_actions = recommended_interactions.filter(
        interaction_type__in=['add_to_shelf', 'purchase']
    ).count()
    recommendation_conversion = (recommendation_actions / recommendation_views * 100) if recommendation_views > 0 else 0

    modalities_metrics = {
        'new_releases_count': new_releases_count,
        'new_releases_percent': new_releases_percent,
        'bestsellers_count': bestsellers_count,
        'bestsellers_total_sales': bestsellers_total_sales,
        'recommended_count': recommended_count,
        'recommended_conversion_rate': recommendation_conversion,
        'catalogue_count': total_books,
    }

    context.update({
        'modalities_metrics': modalities_metrics
    })

    return render(request, 'core/admin_dashboard/metrics.html', context)
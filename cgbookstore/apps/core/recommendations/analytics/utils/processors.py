from django.db.models import Count
from django.db.models.functions import TruncDate


def process_interaction_data(daily_interactions):
    """
    Processa os dados de interações diárias para o formato do Chart.js
    """
    labels = []
    values = []

    for interaction in daily_interactions:
        labels.append(interaction['date'].strftime('%d/%m/%Y'))
        values.append(interaction['count'])

    return {
        'labels': labels,
        'values': values
    }


def process_metrics_data(data, comparison_data=None):
    """
    Processa métricas com comparação opcional com período anterior
    """
    processed = []
    for key, value in data.items():
        metric = {
            'title': key.replace('_', ' ').title(),
            'value': value
        }

        if comparison_data and key in comparison_data:
            old_value = comparison_data[key]
            if old_value > 0:
                change = ((value - old_value) / old_value) * 100
                metric['change'] = round(change, 1)

        processed.append(metric)

    return processed
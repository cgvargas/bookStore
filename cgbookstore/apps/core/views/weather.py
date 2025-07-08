import json
import logging
import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.core.cache import cache, caches

# Tente importar a configuração alternativa
try:
    from ..weather_config import WEATHER_API_KEY as ALTERNATE_KEY
except (ImportError, AttributeError):
    ALTERNATE_KEY = None

logger = logging.getLogger(__name__)

# Tempo de cache em segundos (30 minutos)
CACHE_TIMEOUT = 60 * 30


@require_GET
def get_weather(request):
    """
    View para obter dados meteorológicos de uma API externa.
    Aceita o parâmetro 'location' via query string.
    """
    # Usar o cache específico para dados meteorológicos
    weather_cache = caches['weather']

    location = request.GET.get('location', 'São Paulo')

    try:
        # Verificar se a chave API está configurada
        api_key = getattr(settings, 'WEATHER_API_KEY', '')
        if not api_key:
            logger.error("WEATHER_API_KEY não configurada. Verifique o arquivo .env")
            return JsonResponse({
                'error': 'Chave de API não configurada. Entre em contato com o administrador do sistema.',
                'config_missing': True
            }, status=503)  # 503 Service Unavailable

        # Verificar se temos dados em cache para esta localização
        cache_key = f'weather_data_{location.lower().replace(" ", "_")}'
        cached_data = weather_cache.get(cache_key)

        if cached_data:
            return JsonResponse(cached_data)

        # Se não tiver em cache, buscar na API
        weather_data = fetch_weather_data(location)

        if weather_data:
            # Armazenar em cache para futuras requisições
            weather_cache.set(cache_key, weather_data, CACHE_TIMEOUT)
            return JsonResponse(weather_data)
        else:
            return JsonResponse({
                'error': 'Não foi possível obter os dados meteorológicos'
            }, status=500)

    except Exception as e:
        logger.error(f"Erro ao obter dados meteorológicos: {str(e)}")
        return JsonResponse({
            'error': 'Erro ao processar a solicitação meteorológica'
        }, status=500)


def fetch_weather_data(location):
    """
    Busca dados meteorológicos de uma API externa.
    Utilizando a API WeatherAPI.com como exemplo.
    """
    try:
        # URL da API (exemplo com WeatherAPI.com)
        # Você precisará se registrar para obter uma chave API
        api_key = getattr(settings, 'WEATHER_API_KEY', '')

        # Se não houver chave API configurada, retorne um erro explicativo
        if not api_key:
            logger.error("Chave da API de clima não configurada no settings.py")
            return None

        url = f"https://api.weatherapi.com/v1/current.json?key={api_key}&q={location}&aqi=no"

        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Lança exceção para respostas de erro HTTP

        data = response.json()

        # Extrair e formatar os dados relevantes
        current = data.get('current', {})
        location_data = data.get('location', {})

        weather_data = {
            'city': location_data.get('name', 'Desconhecido'),
            'region': location_data.get('region', ''),
            'country': location_data.get('country', ''),
            'temperature': current.get('temp_c', 0),
            'feels_like': current.get('feelslike_c', 0),
            'humidity': current.get('humidity', 0),
            'wind_speed': current.get('wind_kph', 0),
            'wind_direction': current.get('wind_dir', ''),
            'pressure': current.get('pressure_mb', 0),
            'precipitation': current.get('precip_mm', 0),
            'weather_condition': current.get('condition', {}).get('text', 'Desconhecido'),
            'weather_icon': current.get('condition', {}).get('icon', ''),
            'is_day': bool(current.get('is_day', 1)),
            'last_updated': current.get('last_updated', '')
        }

        return weather_data

    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na requisição à API de clima: {str(e)}")
        return None
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        logger.error(f"Erro ao processar dados da API de clima: {str(e)}")
        return None
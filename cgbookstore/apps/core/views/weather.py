# cgbookstore/apps/core/views/weather.py
"""
View para API de previsão do tempo.
Integra com WeatherAPI para fornecer dados climáticos em tempo real.
"""

import logging
import requests
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)


def get_weather_api_key():
    """
    Obtém a chave da API de clima de diferentes fontes.
    Prioridade: 1. Variável de ambiente, 2. arquivo weather_config.py
    """
    # Primeiro, tenta obter da variável de ambiente
    api_key = getattr(settings, 'WEATHER_API_KEY', None)

    if api_key:
        return api_key

    # Se não encontrou, tenta importar do arquivo weather_config.py
    try:
        from cgbookstore.config import weather_config
        api_key = getattr(weather_config, 'WEATHER_API_KEY', None)
        if api_key:
            logger.info("Usando chave da API de clima de weather_config.py")
            return api_key
    except ImportError:
        logger.warning("Arquivo weather_config.py não encontrado")
    except Exception as e:
        logger.error(f"Erro ao importar weather_config.py: {str(e)}")

    return None


@require_http_methods(["GET"])
def get_weather(request):
    """
    Endpoint para obter dados de previsão do tempo.

    Parâmetros:
        location (str): Nome da cidade

    Retorna:
        JSON com dados do clima ou erro
    """
    try:
        # Obter localização do parâmetro de query
        location = request.GET.get('location', 'Rio de Janeiro')

        if not location:
            return JsonResponse({
                'error': 'Localização não fornecida',
                'success': False
            }, status=400)

        # Verificar se a chave da API está configurada
        api_key = get_weather_api_key()

        if not api_key:
            logger.error("WEATHER_API_KEY não configurada")
            return JsonResponse({
                'error': 'Chave da API de clima não configurada. Verifique as configurações.',
                'config_missing': True,
                'success': False
            }, status=503)

        # URL da API WeatherAPI
        weather_url = "http://api.weatherapi.com/v1/current.json"

        # Parâmetros para a requisição
        params = {
            'key': api_key,
            'q': location,
            'aqi': 'no',
            'lang': 'pt'
        }

        logger.info(f"Buscando clima para: {location}")

        # Fazer requisição para a API
        response = requests.get(weather_url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()

            # Extrair dados relevantes
            weather_data = {
                'success': True,
                'city': data['location']['name'],
                'region': data['location']['region'],
                'country': data['location']['country'],
                'temperature': data['current']['temp_c'],
                'description': data['current']['condition']['text'],
                'humidity': data['current']['humidity'],
                'wind_speed': data['current']['wind_kph'],
                'wind_direction': data['current']['wind_dir'],
                'pressure': data['current']['pressure_mb'],
                'feels_like': data['current']['feelslike_c'],
                'uv_index': data['current']['uv'],
                'visibility': data['current']['vis_km'],
                'weather_condition': data['current']['condition']['text'].lower(),
                'is_day': data['current']['is_day'] == 1,
                'icon_url': f"https:{data['current']['condition']['icon']}",
                'last_updated': data['current']['last_updated']
            }

            logger.info(f"Dados do clima obtidos com sucesso para {location}")
            return JsonResponse(weather_data)

        elif response.status_code == 400:
            # Erro de parâmetros (localização não encontrada)
            error_data = response.json()
            return JsonResponse({
                'error': f'Localização "{location}" não encontrada',
                'details': error_data.get('error', {}).get('message', 'Erro desconhecido'),
                'success': False
            }, status=404)

        elif response.status_code == 401:
            # Chave da API inválida
            logger.error("Chave da API de clima inválida")
            return JsonResponse({
                'error': 'Chave da API de clima inválida',
                'config_missing': True,
                'success': False
            }, status=401)

        elif response.status_code == 403:
            # Limite de requisições excedido
            logger.error("Limite de requisições da API de clima excedido")
            return JsonResponse({
                'error': 'Limite de requisições excedido. Tente novamente mais tarde.',
                'success': False
            }, status=429)

        else:
            # Outros erros da API
            logger.error(f"Erro da API de clima: {response.status_code}")
            return JsonResponse({
                'error': 'Serviço de clima temporariamente indisponível',
                'success': False
            }, status=503)

    except requests.exceptions.Timeout:
        logger.error("Timeout na requisição da API de clima")
        return JsonResponse({
            'error': 'Tempo limite excedido ao buscar dados do clima',
            'success': False
        }, status=504)

    except requests.exceptions.ConnectionError:
        logger.error("Erro de conexão com a API de clima")
        return JsonResponse({
            'error': 'Erro de conexão com o serviço de clima',
            'success': False
        }, status=503)

    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de requisição da API de clima: {str(e)}")
        return JsonResponse({
            'error': 'Erro ao comunicar com o serviço de clima',
            'success': False
        }, status=503)

    except Exception as e:
        logger.error(f"Erro inesperado na API de clima: {str(e)}")
        return JsonResponse({
            'error': 'Erro interno do servidor',
            'success': False
        }, status=500)


@csrf_exempt
def test_weather_config(request):
    """
    Endpoint para testar a configuração da API de clima.
    Útil para debugging em desenvolvimento.
    """
    if not settings.DEBUG:
        return JsonResponse({'error': 'Endpoint disponível apenas em modo debug'}, status=403)

    api_key = get_weather_api_key()

    return JsonResponse({
        'api_key_configured': bool(api_key),
        'api_key_source': 'environment' if getattr(settings, 'WEATHER_API_KEY', None) else 'weather_config.py',
        'api_key_preview': f"{api_key[:8]}..." if api_key else None,
        'debug_mode': settings.DEBUG
    })
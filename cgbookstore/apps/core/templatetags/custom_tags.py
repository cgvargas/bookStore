"""
Módulo de tags customizadas para templates Django.

Fornece filtros personalizados para uso em templates,
expandindo as capacidades de renderização de dados.
"""

from django import template
from decimal import Decimal
from urllib.parse import urlparse, parse_qs
import re

# Registrador de tags customizadas
register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Filtro personalizado para acessar valores de dicionários em templates.

    Permite acesso seguro a valores de dicionários usando chaves dinâmicas,
    retornando string vazia se a chave não existir.

    Exemplo de uso no template:
    {{ my_dict|get_item:'key_name' }}

    Args:
        dictionary (dict): Dicionário para busca
        key (str): Chave para acessar o valor

    Returns:
        Valor correspondente à chave ou string vazia se não encontrado
    """
    return dictionary.get(key, "")

@register.filter
def sub(value, arg):
    """
    Filtro para realizar subtração em templates.

    Permite subtrair valores decimais em templates Django.
    Retorna 0 se algum dos valores for None.

    Args:
        value (Decimal/float): Valor inicial
        arg (Decimal/float): Valor a ser subtraído

    Returns:
        Decimal: Resultado da subtração ou 0 se algum valor for None
    """
    try:
        if value is None or arg is None:
            return Decimal('0')
        return Decimal(str(value)) - Decimal(str(arg))
    except:
        return Decimal('0')

@register.filter
def get_youtube_id(url):
    """
    Extrai o ID do vídeo de uma URL do YouTube.
    Suporta formatos:
    - watch?v=
    - youtu.be/
    - shorts/
    - embed/
    """

    # Tenta extrair do formato padrão youtube.com/watch?v=
    parsed_url = urlparse(url)
    if 'youtube.com' in parsed_url.netloc:
        if 'watch' in parsed_url.path:
            return parse_qs(parsed_url.query).get('v', [''])[0]
        elif 'shorts' in parsed_url.path:
            # Formato shorts
            return parsed_url.path.split('/')[-1]
        elif 'embed' in parsed_url.path:
            # Formato embed
            return parsed_url.path.split('/')[-1]

    # Formato youtu.be
    elif 'youtu.be' in parsed_url.netloc:
        return parsed_url.path.lstrip('/')

    return ''

@register.filter
def get_youtube_thumbnail(video_id):
    """
    Retorna a URL da thumbnail de alta qualidade do YouTube.
    Se não existir, cai para qualidade menor.
    """
    return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
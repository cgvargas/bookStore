"""
Módulo de tags customizadas para templates Django.

Fornece filtros personalizados para uso em templates,
expandindo as capacidades de renderização de dados.
"""

from django import template
from decimal import Decimal
from django.utils.safestring import mark_safe
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
    Extrai o ID do vídeo do YouTube a partir da URL.
    Detecta vários formatos de URL do YouTube.
    """
    if not url:
        return ""

    # Padrão simplificado para extrair o ID
    if 'youtu.be/' in url:
        # Para URLs curtas como youtu.be/VIDEO_ID
        video_id = url.split('youtu.be/')[-1].split('?')[0].split('&')[0]
    elif 'youtube.com/watch' in url:
        # Para URLs padrão com parâmetro v=
        try:
            video_id = re.search(r'v=([^&]+)', url).group(1)
        except:
            video_id = ""
    elif 'youtube.com/embed/' in url:
        # Para URLs de incorporação
        video_id = url.split('youtube.com/embed/')[-1].split('?')[0].split('&')[0]
    elif 'youtube.com/shorts/' in url:
        # Para URLs de shorts
        video_id = url.split('youtube.com/shorts/')[-1].split('?')[0].split('&')[0]
    else:
        video_id = ""

    # Remove qualquer parâmetro adicional do ID
    video_id = video_id.split('?')[0].split('&')[0]

    # Valida o ID (geralmente tem 11 caracteres)
    if video_id and len(video_id) < 5:
        return ""

    return video_id.strip()


@register.filter
def get_youtube_thumbnail(video_id):
    """
    Retorna a URL da imagem de thumbnail do YouTube.
    """
    if not video_id:
        return ""

    # Retorna a versão de alta qualidade do thumbnail
    return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"


@register.filter
def get_thumbnail(book_data):
    """
    Extrai URL da thumbnail de livros do Google Books.

    Acessa dados aninhados de forma segura: book.volumeInfo.imageLinks.thumbnail

    Args:
        book_data (dict): Dados do livro do Google Books

    Returns:
        str: URL da thumbnail ou URL da imagem padrão
    """
    try:
        if isinstance(book_data, dict):
            volume_info = book_data.get('volumeInfo', {})
            image_links = volume_info.get('imageLinks', {})
            thumbnail = image_links.get('thumbnail', '')

            # Converter HTTP para HTTPS se necessário
            if thumbnail and thumbnail.startswith('http://'):
                thumbnail = thumbnail.replace('http://', 'https://')

            return thumbnail
    except (AttributeError, TypeError):
        pass

    return ''


@register.filter
def get_book_title(book_data):
    """
    Extrai título de livros do Google Books de forma segura.

    Args:
        book_data (dict): Dados do livro do Google Books

    Returns:
        str: Título do livro ou "Título desconhecido"
    """
    try:
        if isinstance(book_data, dict):
            volume_info = book_data.get('volumeInfo', {})
            return volume_info.get('title', 'Título desconhecido')
    except (AttributeError, TypeError):
        pass

    return 'Título desconhecido'


@register.filter
def get_book_authors(book_data):
    """
    Extrai autores de livros do Google Books de forma segura.

    Args:
        book_data (dict): Dados do livro do Google Books

    Returns:
        str: Nome do primeiro autor ou "Autor desconhecido"
    """
    try:
        if isinstance(book_data, dict):
            volume_info = book_data.get('volumeInfo', {})
            authors = volume_info.get('authors', [])

            if authors and len(authors) > 0:
                return authors[0]
    except (AttributeError, TypeError):
        pass

    return 'Autor desconhecido'


@register.filter
def get_book_categories(book_data):
    """
    Extrai categorias de livros do Google Books de forma segura.

    Args:
        book_data (dict): Dados do livro do Google Books

    Returns:
        str: Primeira categoria ou string vazia
    """
    try:
        if isinstance(book_data, dict):
            volume_info = book_data.get('volumeInfo', {})
            categories = volume_info.get('categories', [])

            if categories and len(categories) > 0:
                return categories[0]
    except (AttributeError, TypeError):
        pass

    return ''
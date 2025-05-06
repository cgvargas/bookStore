import logging
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

logger = logging.getLogger(__name__)


def standardize_google_book_cover(url, size='M'):
    """ Padroniza o tamanho das capas de livros do Google Books.
    Parâmetros:
    - url: URL original da imagem
    - size: Tamanho desejado ('S' para pequeno, 'M' para médio, 'L' para grande)

    Tamanhos aproximados:
    - S: ~128px
    - M: ~256px
    - L: ~512px
    """
    if not url:
        return ''

    try:
        # Verifica se é uma URL do Google Books
        if 'books.google.com' in url or 'googleusercontent.com' in url:
            # Parse da URL para manipular parâmetros
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)

            # Remove parâmetros de zoom existentes, mas preserva outros parâmetros
            if 'zoom' in query_params:
                del query_params['zoom']

            # Remove edge=curl se presente
            if 'edge' in query_params:
                del query_params['edge']

            # Define o parâmetro de zoom baseado no tamanho desejado
            zoom_level = {
                'S': '1',  # Pequeno
                'M': '2',  # Médio
                'L': '3'  # Grande
            }.get(size.upper(), '2')  # Médio é o padrão

            query_params['zoom'] = [zoom_level]

            # Adiciona parâmetro para qualidade da imagem
            query_params['img'] = ['1']

            # Reconstrói a URL com os parâmetros atualizados
            new_query = urlencode(query_params, doseq=True)
            new_url = urlunparse((
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                parsed_url.params,
                new_query,
                parsed_url.fragment
            ))

            return new_url

        # Se não for uma URL do Google Books, verifica se é uma URL genérica
        elif url.startswith(('http://', 'https://')):
            # Retorna a URL original para outras fontes de imagem
            return url
        else:
            # Se não for uma URL válida, retorna vazio
            logger.warning(f"URL de capa inválida: {url}")
            return ''
    except Exception as e:
        logger.error(f"Erro ao padronizar URL da capa: {str(e)}")
        return url or ''


def get_fallback_cover():
    """Retorna URL para uma imagem de capa padrão quando nenhuma capa está disponível"""
    return '/static/images/no-cover.svg'


def ensure_cover_url(url):
    """Garante que sempre haja uma URL de capa, usando fallback se necessário"""
    if not url or url.strip() == '':
        return get_fallback_cover()
    return url
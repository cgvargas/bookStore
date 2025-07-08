import logging
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

logger = logging.getLogger(__name__)


def standardize_google_book_cover(url, size='M'):
    """
    Padroniza URLs de capas do Google Books para melhor qualidade.
    Adiciona tratamento especial para URLs problemáticas.
    """
    if not url:
        return ''

    # Verificar se é uma URL do Google Books
    if 'books.google.com' in url or 'googleusercontent.com' in url:
        # Extrair o ID do livro
        id_match = re.search(r'[?&]id=([^&]+)', url)
        if id_match:
            book_id = id_match.group(1)

            # Tratamento especial para IDs problemáticos conhecidos
            problematic_ids = ['5y04AwAAQBAJ', 'rC2eswEACAAJ']  # Adicionar outros IDs problemáticos aqui

            if book_id in problematic_ids:
                # Usar URL alternativa para estes IDs
                return f"/image-proxy/?url=https://books.google.com/books/publisher/content/images/frontcover/{book_id}?fife=w600-h900"

            # Processar normalmente se não for um ID problemático
            size_param = 'zoom=1'
            if size == 'L':
                size_param = 'zoom=2'
            elif size == 'XL':
                size_param = 'zoom=3'

            return f"/image-proxy/?url=https://books.google.com/books/content?id={book_id}&printsec=frontcover&img=1&{size_param}&source=gbs_api"

    # Se não for uma URL do Google Books, retornar como está
    return url


def get_fallback_cover():
    """Retorna URL para uma imagem de capa padrão quando nenhuma capa está disponível"""
    return '/static/images/no-cover.svg'


def ensure_cover_url(url):
    """Garante que sempre haja uma URL de capa, usando fallback se necessário"""
    if not url or url.strip() == '':
        return get_fallback_cover()

    # Se for URL do Google Books, padroniza
    if 'books.google.com' in url or 'googleusercontent.com' in url:
        return standardize_google_book_cover(url, 'M')

    return url
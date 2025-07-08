import requests
import logging
import hashlib
import traceback
from django.http import HttpResponse, Http404
from django.shortcuts import redirect
from django.templatetags.static import static
from io import BytesIO
from PIL import Image
import urllib.parse
from django.core.cache import caches
import re
import os
import sys
import json
import time
from django.utils import timezone
from django.utils.cache import patch_response_headers

# Configurar logging mais detalhado
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

# Usar o cache específico para imagens
image_cache = caches['image_proxy']

# Configurações globais melhoradas
CONFIG = {
    'default_fallback': 'images/no-cover.svg',
    'user_agents': [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ],
    'cache_timeout': 2592000,  # 30 dias em segundos (cache mais longo)
    'cache_timeout_failed': 3600,  # 1 hora para URLs que falharam
    'browser_cache_timeout': 86400,  # 24 horas para cache do navegador
    'min_image_size': 3000,  # Reduzido de 5000 para 3000 bytes
    'min_dimensions': (40, 40),  # Reduzido de (50, 50) para (40, 40)
    'domains': [
        'books.google.com',
        'googleusercontent.com',
        'googleapis.com',
        'lh3.googleusercontent.com',
        'lh4.googleusercontent.com',
        'lh5.googleusercontent.com'
    ],
    'retry_count': 4,  # Aumentado de 3 para 4 tentativas
    'request_timeout': 15,  # Aumentado de 10 para 15 segundos
    'cache_version': '2.0',  # Versão do cache para invalidação
}

# Cache para URLs que falharam (evita retry desnecessário)
FAILED_URLS_CACHE = {}
FAILED_URL_TIMEOUT = 3600  # 1 hora


def google_books_image_proxy(request):
    """
    Proxy otimizado e centralizado para imagens do Google Books.
    Versão melhorada com cache inteligente e melhor tratamento de erros.
    """
    image_url = request.GET.get('url', '')
    force_refresh = request.GET.get('refresh', '').lower() == 'true'

    logger.debug(f"Proxy de imagem solicitado para URL: {image_url}")
    logger.debug(f"Force refresh: {force_refresh}")

    # Verificação básica de URL
    if not image_url:
        logger.error("URL não fornecida")
        return redirect(static(CONFIG['default_fallback']))

    # Verificar se URL falhou recentemente (a menos que seja force refresh)
    if not force_refresh and is_url_recently_failed(image_url):
        logger.info(f"URL falhou recentemente, usando fallback: {image_url}")
        return redirect(static(CONFIG['default_fallback']))

    # Garantir que a URL seja tratável
    try:
        # Limpar e normalizar URL
        image_url = normalize_image_url(image_url)

        # Verificação de domínio
        if not is_valid_domain(image_url):
            logger.warning(f"URL de domínio não reconhecido: {image_url}")
            mark_url_as_failed(image_url)
            return redirect(static(CONFIG['default_fallback']))

        # Extrair ID do Google Books
        book_id = extract_google_books_id(image_url)
        logger.debug(f"ID do livro extraído: {book_id}")

        # Gerar chave de cache com versão
        cache_key = generate_cache_key(image_url)
        logger.debug(f"Chave de cache gerada: {cache_key}")

        # Verificar cache (a menos que seja force refresh)
        if not force_refresh:
            cached_result = get_cached_image(cache_key)
            if cached_result:
                content_type, image_data, cache_info = cached_result
                logger.info(f"Retornando imagem em cache para: {image_url[:60]}...")

                # Adicionar headers de cache para o navegador
                response = HttpResponse(image_data, content_type=content_type)
                add_cache_headers(response)
                return response

        logger.debug("Cache miss ou refresh forçado. Buscando imagem da fonte...")

        # Gerar lista de URLs para tentar
        urls_to_try = generate_candidate_urls(image_url, book_id)
        logger.debug(f"Tentando {len(urls_to_try)} URLs diferentes")

        # Tentar cada URL com estratégia melhorada
        result = try_fetch_image(urls_to_try)

        if result:
            content_type, image_data, successful_url = result

            # Armazenar no cache com metadados
            cache_data = (content_type, image_data, {
                'timestamp': timezone.now().isoformat(),
                'successful_url': successful_url,
                'original_url': image_url
            })

            image_cache.set(cache_key, cache_data, timeout=CONFIG['cache_timeout'])

            # Remover da lista de URLs falhadas se estava lá
            remove_failed_url(image_url)

            logger.info(f"Sucesso! Retornando imagem de: {successful_url[:60]}...")

            # Retornar resposta com headers de cache
            response = HttpResponse(image_data, content_type=content_type)
            add_cache_headers(response)
            return response
        else:
            # Marcar URL como falhada
            mark_url_as_failed(image_url)
            logger.error(f"Todas as tentativas falharam para: {image_url}")
            return redirect(static(CONFIG['default_fallback']))

    except Exception as e:
        logger.error(f"Erro crítico no proxy de imagem: {str(e)}")
        traceback.print_exc()
        mark_url_as_failed(image_url)
        return redirect(static(CONFIG['default_fallback']))


def normalize_image_url(url):
    """
    Normaliza e limpa a URL da imagem.
    """
    url = url.strip()

    # Normalizar protocolo para HTTPS
    if url.startswith('http://'):
        url = 'https://' + url[7:]

    # Remover parâmetros desnecessários que podem causar problemas
    unwanted_params = ['utm_source', 'utm_medium', 'utm_campaign']
    if '?' in url:
        base_url, query_string = url.split('?', 1)
        params = []
        for param in query_string.split('&'):
            if '=' in param:
                key = param.split('=')[0]
                if key not in unwanted_params:
                    params.append(param)

        if params:
            url = base_url + '?' + '&'.join(params)
        else:
            url = base_url

    return url


def is_valid_domain(url):
    """
    Verifica se a URL é de um domínio válido.
    """
    return any(domain in url for domain in CONFIG['domains'])


def generate_cache_key(url):
    """
    Gera chave de cache com versão para permitir invalidação.
    """
    url_hash = hashlib.md5(url.encode()).hexdigest()
    return f"img_proxy_{CONFIG['cache_version']}_{url_hash}"


def get_cached_image(cache_key):
    """
    Recupera imagem do cache com validação.
    """
    try:
        cached_data = image_cache.get(cache_key)
        if cached_data:
            if len(cached_data) == 3:
                # Formato novo com metadados
                content_type, image_data, cache_info = cached_data
                return cached_data
            elif len(cached_data) == 2:
                # Formato antigo sem metadados
                content_type, image_data = cached_data
                return (content_type, image_data, {})
    except Exception as e:
        logger.warning(f"Erro ao recuperar do cache {cache_key}: {str(e)}")
        # Remover entrada corrompida
        image_cache.delete(cache_key)

    return None


def add_cache_headers(response):
    """
    Adiciona headers de cache otimizados para o navegador.
    """
    # Cache no navegador por 24 horas
    patch_response_headers(response, cache_timeout=CONFIG['browser_cache_timeout'])

    # Headers adicionais
    response['Cache-Control'] = f'public, max-age={CONFIG["browser_cache_timeout"]}, stale-while-revalidate=86400'
    response['Vary'] = 'Accept-Encoding'

    return response


def try_fetch_image(urls_to_try):
    """
    Tenta buscar imagem de uma lista de URLs com estratégia melhorada.
    """
    for i, url in enumerate(urls_to_try):
        logger.debug(f"Tentando URL {i + 1}/{len(urls_to_try)}: {url[:60]}...")

        for attempt in range(CONFIG['retry_count']):
            try:
                # Delay progressivo entre tentativas
                if attempt > 0:
                    delay = attempt * 0.5
                    logger.debug(f"Aguardando {delay}s antes da tentativa {attempt + 1}")
                    time.sleep(delay)

                headers = get_request_headers(url, attempt)

                # Fazer requisição com timeout aumentado
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=CONFIG['request_timeout'],
                    stream=True  # Stream para grandes imagens
                )

                if response.status_code != 200:
                    logger.warning(f"Status {response.status_code} para URL: {url[:50]}...")
                    continue

                # Verificar content-type
                content_type = response.headers.get('Content-Type', '')
                if not content_type.startswith('image/'):
                    logger.warning(f"Content-type não é imagem: {content_type}")
                    continue

                # Ler conteúdo
                image_data = response.content

                # Verificar tamanho mínimo
                if len(image_data) < CONFIG['min_image_size']:
                    logger.warning(f"Imagem muito pequena: {len(image_data)} bytes")
                    continue

                # Validar imagem
                if validate_image(image_data):
                    logger.info(f"Sucesso na URL: {url[:50]}... (tentativa {attempt + 1})")
                    return (content_type, image_data, url)
                else:
                    logger.warning(f"Imagem inválida de: {url[:50]}...")
                    continue

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout na URL: {url[:50]}... (tentativa {attempt + 1})")
                continue
            except requests.exceptions.RequestException as e:
                logger.warning(f"Erro de requisição para {url[:50]}...: {str(e)}")
                continue
            except Exception as e:
                logger.warning(f"Erro inesperado para {url[:50]}...: {str(e)}")
                continue

    return None


def validate_image(image_data):
    """
    Valida se os dados representam uma imagem válida.
    """
    try:
        img = Image.open(BytesIO(image_data))
        img.load()  # Força o carregamento para validar
        width, height = img.size

        logger.debug(f"Imagem válida: tamanho={width}x{height}, formato={img.format}")

        # Verificar dimensões mínimas
        if width < CONFIG['min_dimensions'][0] or height < CONFIG['min_dimensions'][1]:
            logger.warning(f"Dimensões insuficientes: {width}x{height}")
            return False

        # Verificar se não é uma imagem de erro/placeholder comum
        if is_error_placeholder(img, image_data):
            logger.warning("Detectada imagem de erro/placeholder")
            return False

        return True

    except Exception as e:
        logger.warning(f"Erro ao validar imagem: {str(e)}")
        return False


def is_error_placeholder(img, image_data):
    """
    Detecta se a imagem é um placeholder de erro comum.
    """
    try:
        width, height = img.size

        # Imagens muito pequenas são suspeitas
        if width <= 1 or height <= 1:
            return True

        # Imagens 1x1 pixel (tracking pixels)
        if width == 1 and height == 1:
            return True

        # Verificar tamanho de arquivo muito pequeno
        if len(image_data) < 500:  # Menos que 500 bytes
            return True

        # Verificar formato suspeito
        if img.format in ['GIF'] and len(image_data) < 1000:
            return True

        return False

    except Exception:
        return True


def is_url_recently_failed(url):
    """
    Verifica se a URL falhou recentemente.
    """
    if url in FAILED_URLS_CACHE:
        failed_time = FAILED_URLS_CACHE[url]
        if time.time() - failed_time < FAILED_URL_TIMEOUT:
            return True
        else:
            # Remove entrada expirada
            del FAILED_URLS_CACHE[url]
    return False


def mark_url_as_failed(url):
    """
    Marca uma URL como falhada.
    """
    FAILED_URLS_CACHE[url] = time.time()

    # Limpar cache de URLs falhadas se ficar muito grande
    if len(FAILED_URLS_CACHE) > 1000:
        # Manter apenas as mais recentes
        current_time = time.time()
        FAILED_URLS_CACHE.clear()


def remove_failed_url(url):
    """
    Remove URL da lista de falhadas.
    """
    if url in FAILED_URLS_CACHE:
        del FAILED_URLS_CACHE[url]


def extract_google_books_id(url):
    """
    Extrai o ID do Google Books de uma URL de forma robusta.
    Versão melhorada com mais padrões.
    """
    try:
        # Padrão principal: id=<ID>
        id_match = re.search(r'[?&]id=([^&]+)', url)
        if id_match:
            return id_match.group(1)

        # Padrão alternativo: books/content/images/<ID>
        alt_match = re.search(r'books/content/images/([^/?&]+)', url)
        if alt_match:
            return alt_match.group(1)

        # Padrão de URL canônica: books.google.com/books?id=<ID>
        canon_match = re.search(r'books\.google\.com/books\?id=([^&]+)', url)
        if canon_match:
            return canon_match.group(1)

        # Padrão para frontcover
        frontcover_match = re.search(r'frontcover/([^/?&]+)', url)
        if frontcover_match:
            return frontcover_match.group(1)

        # Padrão para URLs do tipo books.google.com/books/about/<TÍTULO>/<ID>
        about_match = re.search(r'books/about/[^/]+/([^/?&]+)', url)
        if about_match:
            return about_match.group(1)

        # Padrão para URLs externas com formato diferente
        external_match = re.search(r'books/external/([^/]+)', url)
        if external_match:
            return external_match.group(1)

        # Extração direta de ID do final da URL (IDs do Google Books são alfanuméricos)
        end_match = re.search(r'/([A-Za-z0-9_-]{10,})(?:/|$|\?)', url)
        if end_match:
            potential_id = end_match.group(1)
            # Verificar se parece um ID do Google Books
            if re.match(r'^[A-Za-z0-9_-]+$', potential_id):
                return potential_id

        return None
    except Exception as e:
        logger.error(f"Erro ao extrair ID do livro: {str(e)}")
        return None


def generate_candidate_urls(base_url, book_id):
    """
    Gera uma lista de URLs candidatas para tentar buscar a imagem.
    Versão melhorada com mais variações e ordenação inteligente.
    """
    urls = []

    # Adicionar URL original
    urls.append(base_url)

    # Se temos um ID, gerar variações padronizadas
    if book_id:
        # URLs principais em ordem de prioridade
        priority_urls = [
            # Formato mais confiável com fife
            f"https://books.google.com/books/content?id={book_id}&printsec=frontcover&img=1&zoom=1&source=gbs_api&fife=w400-h600",

            # Formato publisher (geralmente mais estável)
            f"https://books.google.com/books/publisher/content/images/frontcover/{book_id}?fife=w400-h600",

            # Formato com edge=curl (para algumas capas específicas)
            f"https://books.google.com/books/content?id={book_id}&printsec=frontcover&img=1&zoom=1&source=gbs_api&edge=curl&fife=w400-h600",
        ]

        # URLs secundárias
        secondary_urls = [
            # Diferentes níveis de zoom
            f"https://books.google.com/books/content?id={book_id}&printsec=frontcover&img=1&zoom=0&source=gbs_api",
            f"https://books.google.com/books/content?id={book_id}&printsec=frontcover&img=1&zoom=2&source=gbs_api",
            f"https://books.google.com/books/content?id={book_id}&printsec=frontcover&img=1&zoom=3&source=gbs_api",

            # Formato canônico
            f"https://books.google.com/books?id={book_id}&printsec=frontcover&img=1&zoom=1",

            # Formatos alternativos
            f"https://books.google.com/books/content?id={book_id}&pg=PP1&img=1&zoom=1",
            f"https://books.google.com/books/publisher/content/images/frontcover/{book_id}?fife=w240-h360",

            # URLs do GoogleUserContent
            f"https://lh3.googleusercontent.com/books/content?id={book_id}&printsec=frontcover&img=1&zoom=1",
            f"https://lh4.googleusercontent.com/books/content?id={book_id}&printsec=frontcover&img=1&zoom=1",
        ]

        # Adicionar URLs na ordem de prioridade
        urls.extend(priority_urls)
        urls.extend(secondary_urls)

    # Verificar casos especiais
    special_urls = handle_special_cases(book_id)
    if special_urls:
        urls.extend(special_urls)

    # Tratamento especial para formatos de ID problemáticos
    if book_id:
        # Para IDs com caracteres especiais
        if '-' in book_id or '_' in book_id:
            special_id = book_id.replace('-', '').replace('_', '')
            urls.extend([
                f"https://books.google.com/books/content?id={special_id}&printsec=frontcover&img=1&zoom=1&source=gbs_api&fife=w400-h600",
                f"https://books.google.com/books/publisher/content/images/frontcover/{special_id}?fife=w400-h600"
            ])

        # Para IDs curtos, tentar formatos alternativos
        if len(book_id) < 10:
            urls.extend([
                f"https://books.googleusercontent.com/books/content?id={book_id}&printsec=frontcover&img=1&zoom=1",
                f"https://lh3.googleusercontent.com/books/content?id={book_id}&printsec=frontcover&img=1&zoom=1"
            ])

    # Remover duplicatas mantendo a ordem
    seen = set()
    unique_urls = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    logger.debug(f"Total de {len(unique_urls)} URLs únicas a serem tentadas")
    return unique_urls


def get_request_headers(url, attempt=0):
    """
    Gera headers otimizados para a requisição HTTP.
    Versão melhorada com headers mais realistas.
    """
    user_agent = CONFIG['user_agents'][attempt % len(CONFIG['user_agents'])]

    headers = {
        'User-Agent': user_agent,
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Referer': 'https://books.google.com/',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Sec-Fetch-Dest': 'image',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Site': 'cross-site',
    }

    # Adicionar headers específicos para o Google Books
    if 'books.google.com' in url:
        headers.update({
            'Origin': 'https://books.google.com',
            'X-Requested-With': 'XMLHttpRequest',
        })

    return headers


def handle_special_cases(book_id):
    """
    Trata casos especiais conhecidos com URLs alternativas específicas.
    Versão expandida com mais casos problemáticos.
    """
    special_cases = {
        # Casos conhecidos problemáticos
        'rC2eswEACAAJ': [
            'https://books.google.com/books/content?id=rC2eswEACAAJ&printsec=frontcover&img=1&zoom=0',
            'https://books.google.com/books/content?id=rC2eswEACAAJ&printsec=frontcover&img=1&zoom=1',
            'https://books.google.com/books/publisher/content/images/frontcover/rC2eswEACAAJ?fife=w400-h600'
        ],
        'sFE4nwEACAAJ': [
            'https://books.google.com/books/content?id=sFE4nwEACAAJ&printsec=frontcover&img=1&zoom=0',
            'https://books.google.com/books/content?id=sFE4nwEACAAJ&printsec=frontcover&img=1&zoom=1',
            'https://books.google.com/books/publisher/content/images/frontcover/sFE4nwEACAAJ?fife=w400-h600'
        ],
        '5y04AwAAQBAJ': [
            'https://books.google.com/books/content?id=5y04AwAAQBAJ&printsec=frontcover&img=1&zoom=0',
            'https://books.google.com/books/content?id=5y04AwAAQBAJ&printsec=frontcover&img=1&zoom=1&source=gbs_api',
            'https://books.google.com/books/publisher/content/images/frontcover/5y04AwAAQBAJ?fife=w240-h360',
            'https://lh3.googleusercontent.com/books/content?id=5y04AwAAQBAJ&printsec=frontcover&img=1&zoom=1'
        ]
    }

    if book_id and book_id in special_cases:
        logger.debug(f"Aplicando caso especial para ID: {book_id}")
        return special_cases[book_id]

    return []


def debug_problematic_books(url, book_id=None):
    """
    Função específica para debug de livros problemáticos.
    Versão melhorada com mais informações.
    """
    logger.debug("=" * 60)
    logger.debug(f"DEBUG DE LIVRO PROBLEMÁTICO")
    logger.debug(f"URL Original: {url}")
    logger.debug(f"ID Extraído: {book_id}")
    logger.debug(f"Timestamp: {timezone.now().isoformat()}")

    # Verificar casos conhecidos problemáticos
    problematic_ids = ['5y04AwAAQBAJ', 'rC2eswEACAAJ', 'sFE4nwEACAAJ']
    if book_id in problematic_ids:
        logger.debug(f"LIVRO PROBLEMÁTICO CONHECIDO DETECTADO: {book_id}")

    # Extrair e analisar componentes da URL
    if '?' in url:
        base_url, query_string = url.split('?', 1)
        logger.debug(f"Base URL: {base_url}")
        logger.debug(f"Query String: {query_string}")

        params = {}
        for pair in query_string.split('&'):
            if '=' in pair:
                k, v = pair.split('=', 1)
                params[k] = urllib.parse.unquote(v)

        logger.debug(f"Parâmetros decodificados: {json.dumps(params, indent=2)}")

    logger.debug("=" * 60)
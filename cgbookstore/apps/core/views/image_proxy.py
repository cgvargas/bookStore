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


def google_books_image_proxy(request):
    """
    Proxy otimizado para imagens do Google Books usando cache dedicado.
    Versão com logging aprimorado para diagnóstico de problemas.
    """
    image_url = request.GET.get('url', '')

    logger.debug(f"Proxy de imagem solicitado para URL: {image_url}")

    # Verificação básica de URL
    if not image_url:
        logger.error("URL não fornecida")
        return redirect(static('images/no-cover.svg'))

    # Garantir que a URL seja tratável (algumas URLs podem conter caracteres problemáticos)
    try:
        # Limpar URL: remover espaços e caracteres problemáticos
        image_url = image_url.strip()

        # Verificação de domínio mais permissiva
        valid_domains = ['books.google.com', 'googleusercontent.com', 'googleapis.com']
        if not any(domain in image_url for domain in valid_domains):
            logger.warning(f"URL de domínio não reconhecido: {image_url}")
            return redirect(static('images/no-cover.svg'))

        # Gerar uma chave de cache baseada na URL da imagem usando MD5 para mais consistência
        cache_key = f"img_proxy_{hashlib.md5(image_url.encode()).hexdigest()}"
        logger.debug(f"Chave de cache gerada: {cache_key}")

        # Verificar se a imagem já está em cache
        logger.debug("Verificando cache...")
        cached_data = image_cache.get(cache_key)
        if cached_data:
            try:
                logger.info(f"Retornando imagem em cache para: {image_url}")
                content_type, image_data = cached_data
                return HttpResponse(image_data, content_type=content_type)
            except Exception as e:
                logger.warning(f"Erro ao recuperar do cache: {str(e)}")
                # Remover entrada de cache potencialmente corrompida
                image_cache.delete(cache_key)
                logger.debug("Cache corrompido removido.")

        logger.debug("Cache miss. Buscando imagem da fonte...")

        # Lista de URLs alternativas para tentar
        urls_to_try = []

        # URL original (descodificada)
        decoded_url = urllib.parse.unquote(image_url)
        logger.debug(f"URL decodificada: {decoded_url}")

        # 1. URL original com parâmetros extras
        url_with_params = add_google_books_params(decoded_url)
        urls_to_try.append(url_with_params)

        # 2. URL sem token imgtk (que pode expirar)
        base_url = re.sub(r'&imgtk=[^&]+', '', decoded_url)
        if base_url != decoded_url:
            logger.debug(f"URL sem token: {base_url}")
            urls_to_try.append(add_google_books_params(base_url))

        # 3. URLs com diferentes zooms
        for zoom in [1, 2, 3, 0]:
            zoom_url = re.sub(r'zoom=\d+', f'zoom={zoom}', decoded_url)
            if zoom_url != decoded_url:
                logger.debug(f"URL com zoom {zoom}: {zoom_url}")
                urls_to_try.append(add_google_books_params(zoom_url))

        # 4. URL simples sem parâmetros exceto ID
        if 'id=' in decoded_url:
            id_match = re.search(r'id=([^&]+)', decoded_url)
            if id_match:
                book_id = id_match.group(1)
                logger.debug(f"ID do livro extraído: {book_id}")

                # Várias opções de URL para o Google Books
                for zoom in [1, 2, 0]:
                    simple_url = f"https://books.google.com/books/content?id={book_id}&printsec=frontcover&img=1&zoom={zoom}"
                    urls_to_try.append(simple_url)

                # Tenta também com outros parâmetros
                urls_to_try.append(
                    f"https://books.google.com/books/publisher/content/images/frontcover/{book_id}?fife=w400-h600")
                urls_to_try.append(f"https://books.google.com/books?id={book_id}&printsec=frontcover&img=1&zoom=1")

        # Remover URLs duplicadas mantendo a ordem
        unique_urls = []
        for url in urls_to_try:
            if url not in unique_urls:
                unique_urls.append(url)

        urls_to_try = unique_urls
        logger.debug(f"Total de {len(urls_to_try)} URLs a serem tentadas")

        # Tentar cada URL na lista
        for index, url_to_try in enumerate(urls_to_try):
            try:
                logger.debug(f"Tentativa {index + 1}/{len(urls_to_try)}: {url_to_try}")

                # Configurar os headers para simular um navegador real
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
                    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Referer': 'https://books.google.com/',
                    'Cache-Control': 'no-cache',
                }

                # Fazer requisição para a imagem
                logger.debug(f"Iniciando requisição HTTP para: {url_to_try}")
                response = requests.get(url_to_try, headers=headers, timeout=10)
                logger.debug(
                    f"Resposta HTTP: status={response.status_code}, tipo={response.headers.get('Content-Type', 'desconhecido')}, tamanho={len(response.content)} bytes")

                if response.status_code != 200:
                    logger.warning(f"Erro HTTP {response.status_code} para URL: {url_to_try}")
                    continue

                # Verificar o tipo de conteúdo
                content_type = response.headers.get('Content-Type', '')

                # Se for uma imagem, processar
                if content_type.startswith('image/'):
                    logger.debug(f"Conteúdo de imagem recebido: {content_type}")

                    # Verificar se a imagem é válida com tratamento de exceções robusto
                    try:
                        img_data = BytesIO(response.content)
                        img = Image.open(img_data)

                        # Em vez de verify(), apenas tentar carregar para memória
                        # que pode ser mais confiável em algumas situações
                        img.load()

                        width, height = img.size
                        logger.debug(f"Imagem válida: tamanho={width}x{height}, formato={img.format}")

                        # Verificar tamanho mínimo - mas ser mais permissivo
                        if width < 10 or height < 10:
                            logger.warning(f"Imagem muito pequena: {width}x{height}")
                            continue

                        # Verificar se não é uma imagem vazia ou de erro
                        # Isso pode ser detectado por tamanho muito pequeno (alguns KB)
                        if len(response.content) < 1000:  # menos de 1KB
                            logger.warning(f"Imagem suspeita (muito pequena): {len(response.content)} bytes")
                            continue

                        # Armazenar no cache específico para imagens
                        logger.debug(
                            f"Armazenando imagem no cache: key={cache_key}, tamanho={len(response.content)} bytes")
                        image_cache.set(cache_key, (content_type, response.content))

                        # Retornar a imagem como resposta
                        logger.info(f"Sucesso! Retornando imagem: {url_to_try}")
                        return HttpResponse(response.content, content_type=content_type)

                    except Exception as e:
                        logger.warning(f"Erro ao processar imagem: {str(e)}")
                        traceback.print_exc()
                        continue

                else:
                    logger.warning(f"Tipo de conteúdo não suportado: {content_type}")
                    continue

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout ao acessar URL: {url_to_try}")
                continue
            except requests.exceptions.RequestException as e:
                logger.warning(f"Erro de requisição para URL {url_to_try}: {str(e)}")
                continue
            except Exception as e:
                logger.error(f"Erro não esperado ao processar URL {url_to_try}: {str(e)}")
                traceback.print_exc()
                continue

        # Se nenhuma das tentativas funcionou, retornar a imagem padrão
        logger.error(f"Todas as {len(urls_to_try)} tentativas falharam para a imagem: {image_url}")
        return redirect(static('images/no-cover.svg'))

    except Exception as e:
        logger.error(f"Erro crítico no proxy de imagem: {str(e)}")
        traceback.print_exc()
        return redirect(static('images/no-cover.svg'))


def add_google_books_params(url):
    """Adiciona parâmetros que melhoram a chance de obter a imagem"""
    try:
        # Parâmetros que ajudam a obter melhor qualidade
        extra_params = {
            'zoom': '1',
            'img': '1',
            'source': 'gbs_api',
            'fife': 'w400-h600',
        }

        # Separar a URL base dos parâmetros existentes
        if '?' in url:
            base_url, params_str = url.split('?', 1)
            params = dict(urllib.parse.parse_qsl(params_str))
        else:
            base_url = url
            params = {}

        # Adicionar novos parâmetros apenas se não existirem
        for key, value in extra_params.items():
            if key not in params:
                params[key] = value

        # Reconstruir a URL com todos os parâmetros
        encoded_params = urllib.parse.urlencode(params)
        return f"{base_url}?{encoded_params}"
    except Exception as e:
        logger.error(f"Erro ao adicionar parâmetros à URL: {str(e)}")
        return url  # Retorna a URL original em caso de erro
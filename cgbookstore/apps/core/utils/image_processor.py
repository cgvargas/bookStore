from PIL import Image
from io import BytesIO
from django.core.files import File
import os
import requests
import logging

logger = logging.getLogger(__name__)


def get_high_quality_cover(thumbnail_url: str) -> str:
    """
    Tenta obter a versão em alta qualidade da capa do livro.
    Se não conseguir, retorna a URL original da thumbnail.
    """
    try:
        # Tenta obter versão em alta qualidade
        hq_url = thumbnail_url.replace('zoom=1', 'zoom=0').replace('&edge=curl', '')
        response = requests.head(hq_url, timeout=5)

        # Se a imagem em alta qualidade existe e tem tamanho válido
        if response.status_code == 200 and int(response.headers.get('content-length', 0)) > 10000:
            return hq_url

        # Se não encontrou versão em alta qualidade, retorna thumbnail original
        return thumbnail_url

    except Exception as e:
        logger.error(f"Erro ao tentar obter capa em alta qualidade: {e}")
        return thumbnail_url


def process_book_cover(instance, filename):
    """
    Processa a imagem da capa do livro, criando uma versão em alta qualidade
    e um preview otimizado.
    """
    if not instance.capa:
        return

    # Abre a imagem usando PIL
    img = Image.open(instance.capa)

    # Converte para RGB se necessário
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # Processa a imagem principal (capa)
    max_size = (800, 1200)  # Tamanho máximo mantendo proporção
    img.thumbnail(max_size, Image.Resampling.LANCZOS)

    # Salva a capa processada
    output = BytesIO()
    img.save(output, format='JPEG', quality=95, optimize=True)
    output.seek(0)

    # Atualiza o campo capa
    instance.capa = File(output, name=filename)

    # Cria preview
    preview_size = (400, 600)
    preview = img.copy()
    preview.thumbnail(preview_size, Image.Resampling.LANCZOS)

    # Salva o preview
    preview_output = BytesIO()
    preview.save(preview_output, format='JPEG', quality=85, optimize=True)
    preview_output.seek(0)

    # Gera nome para o preview
    name, ext = os.path.splitext(filename)
    preview_name = f"{name}_preview{ext}"

    # Atualiza o campo capa_preview
    instance.capa_preview = File(preview_output, name=preview_name)
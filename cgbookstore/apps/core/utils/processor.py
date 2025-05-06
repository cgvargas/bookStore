"""
Módulo de processamento de imagens para capas de livros.

Fornece utilitários para:
- Obtenção de capas em alta qualidade
- Processamento e otimização de imagens de livros
- Criação de previews otimizados
"""

from PIL import Image
from io import BytesIO
from django.core.files import File
import os
import requests
import logging

# Configuração de logger para rastreamento de eventos de processamento de imagem
logger = logging.getLogger(__name__)


def get_high_quality_cover(thumbnail_url: str) -> str:
    """
    Tenta obter a versão em alta qualidade da capa do livro.

    Características:
    - Modifica URL para buscar versão de maior resolução
    - Verifica existência e tamanho da imagem
    - Fallback para URL original em caso de falha

    Args:
        thumbnail_url (str): URL da miniatura da capa

    Returns:
        str: URL da capa em alta qualidade ou URL original
    """
    try:
        # Tenta obter versão em alta qualidade
        # Substitui parâmetros de zoom e remove efeitos de borda
        hq_url = thumbnail_url.replace('zoom=1', 'zoom=0').replace('&edge=curl', '')

        # Verifica existência da imagem com timeout
        response = requests.head(hq_url, timeout=5)

        # Valida imagem: código 200 e tamanho mínimo
        if response.status_code == 200 and int(response.headers.get('content-length', 0)) > 10000:
            return hq_url

        # Se não encontrou versão em alta qualidade, retorna thumbnail original
        return thumbnail_url

    except Exception as e:
        # Registra erro e retorna URL original
        logger.error(f"Erro ao tentar obter capa em alta qualidade: {e}")
        return thumbnail_url


def process_book_cover(instance, filename):
    """
    Processa a imagem da capa do livro.

    Etapas de processamento:
    1. Abre e converte imagem para RGB
    2. Redimensiona capa principal
    3. Salva capa otimizada
    4. Cria preview reduzido
    5. Salva preview otimizado

    Args:
        instance: Instância do modelo de livro
        filename (str): Nome original do arquivo

    Características:
    - Mantém proporção da imagem
    - Utiliza algoritmo de redimensionamento de alta qualidade
    - Ajusta qualidade de compressão
    - Cria preview separado
    """
    # Verifica se existe imagem de capa
    if not instance.capa:
        return

    # Abre a imagem usando PIL
    img = Image.open(instance.capa)

    # Converte para RGB se necessário
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # Processa a imagem principal (capa)
    # Define tamanho máximo mantendo proporção
    max_size = (800, 1200)
    img.thumbnail(max_size, Image.Resampling.LANCZOS)

    # Salva a capa processada em buffer de memória
    output = BytesIO()
    img.save(output, format='JPEG', quality=95, optimize=True)
    output.seek(0)

    # Atualiza o campo capa
    instance.capa = File(output, name=filename)

    # Cria preview
    # Tamanho reduzido para visualização rápida
    preview_size = (400, 600)
    preview = img.copy()
    preview.thumbnail(preview_size, Image.Resampling.LANCZOS)

    # Salva o preview em buffer de memória
    preview_output = BytesIO()
    preview.save(preview_output, format='JPEG', quality=85, optimize=True)
    preview_output.seek(0)

    # Gera nome para o preview
    # Adiciona sufixo '_preview' ao nome original
    name, ext = os.path.splitext(filename)
    preview_name = f"{name}_preview{ext}"

    # Atualiza o campo capa_preview
    instance.capa_preview = File(preview_output, name=preview_name)
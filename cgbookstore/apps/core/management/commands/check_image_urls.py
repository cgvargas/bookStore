import requests
from django.core.management.base import BaseCommand
from io import BytesIO
from PIL import Image
import logging
import sys

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


class Command(BaseCommand):
    help = 'Verifica URLs de imagens para diagnóstico'

    def add_arguments(self, parser):
        parser.add_argument('urls', nargs='+', type=str, help='URLs das imagens para verificar')

    def handle(self, *args, **options):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://books.google.com/',
        }

        for url in options['urls']:
            self.stdout.write(f'\nVerificando URL: {url}')

            try:
                response = requests.get(url, headers=headers, timeout=10)
                self.stdout.write(f'Status: {response.status_code}')
                self.stdout.write(f'Tipo de conteúdo: {response.headers.get("Content-Type")}')
                self.stdout.write(f'Tamanho: {len(response.content)} bytes')

                if response.status_code == 200 and response.headers.get('Content-Type', '').startswith('image/'):
                    try:
                        img_data = BytesIO(response.content)
                        img = Image.open(img_data)
                        img.load()
                        self.stdout.write(
                            self.style.SUCCESS(f'Imagem válida: {img.width}x{img.height}, formato={img.format}'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Erro ao processar imagem: {str(e)}'))
                else:
                    self.stdout.write(self.style.WARNING('Não é uma imagem válida ou status não é 200'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Erro: {str(e)}'))
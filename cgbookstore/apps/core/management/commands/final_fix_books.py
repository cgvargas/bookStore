import json
import os
import requests
from django.core.management.base import BaseCommand
from django.core.cache import caches
from django.db.models import Q
from cgbookstore.apps.core.models.book import Book
from django.conf import settings
from PIL import Image
from io import BytesIO
import time


class Command(BaseCommand):
    help = 'Solução completa para problemas de capa de livros'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Forçar atualização de todos os livros')

    def handle(self, *args, **options):
        force = options.get('force', False)

        self.stdout.write(self.style.SUCCESS('=== INICIANDO CORREÇÃO COMPLETA DE CAPAS DE LIVROS ==='))

        # 1. Limpar todos os caches
        self.clear_all_caches()

        # 2. Corrigir todos os livros com HTTP em URLs
        self.fix_http_urls()

        # 3. Corrigir livros específicos
        self.fix_specific_books()

        # 4. Verificar e baixar imagens para livros sem capa
        self.download_missing_covers(force=force)

        # 5. Verificar todos os livros com verificação de imagem
        self.verify_all_books(force=force)

        self.stdout.write(self.style.SUCCESS('=== CORREÇÃO COMPLETA FINALIZADA ==='))

    def clear_all_caches(self):
        """Limpa todos os caches relacionados"""
        self.stdout.write(self.style.WARNING('Limpando todos os caches...'))

        cache_names = ['default', 'image_proxy', 'google_books', 'books_recommendations']
        for cache_name in cache_names:
            try:
                caches[cache_name].clear()
                self.stdout.write(self.style.SUCCESS(f'Cache "{cache_name}" limpo com sucesso'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Erro ao limpar cache "{cache_name}": {str(e)}'))

    def fix_http_urls(self):
        """Corrige todas as URLs que começam com HTTP para HTTPS"""
        self.stdout.write(self.style.WARNING('Corrigindo URLs HTTP -> HTTPS...'))

        # Corrigir URLs de capa
        books_with_http = Book.objects.filter(capa_url__startswith='http://')
        count = books_with_http.count()
        self.stdout.write(f'Encontrados {count} livros com URLs HTTP')

        for book in books_with_http:
            old_url = book.capa_url
            new_url = old_url.replace('http://', 'https://')
            book.capa_url = new_url
            book.save(update_fields=['capa_url'])
            self.stdout.write(f'  Corrigido: Livro {book.id} - {book.titulo}')

        # Corrigir URLs em dados externos
        books_with_external = Book.objects.exclude(external_data='').exclude(external_data__isnull=True)
        self.stdout.write(f'Verificando {books_with_external.count()} livros com dados externos')

        for book in books_with_external:
            try:
                if 'http://' in book.external_data:
                    data = json.loads(book.external_data)
                    modified = False

                    # Verificar e atualizar links de imagem
                    if 'volumeInfo' in data and 'imageLinks' in data['volumeInfo']:
                        for key, url in data['volumeInfo']['imageLinks'].items():
                            if isinstance(url, str) and url.startswith('http://'):
                                data['volumeInfo']['imageLinks'][key] = url.replace('http://', 'https://')
                                modified = True

                    if modified:
                        book.external_data = json.dumps(data)
                        book.save(update_fields=['external_data'])
                        self.stdout.write(f'  Corrigidos dados externos: Livro {book.id} - {book.titulo}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Erro ao processar dados externos do livro {book.id}: {str(e)}'))

    def fix_specific_books(self):
        """Corrige livros problemáticos específicos"""
        self.stdout.write(self.style.WARNING('Corrigindo livros problemáticos específicos...'))

        # Lista de IDs externos problemáticos conhecidos
        problem_ids = ['rC2eswEACAAJ', 'sFE4nwEACAAJ']

        for external_id in problem_ids:
            books = Book.objects.filter(external_id=external_id)
            for book in books:
                self.stdout.write(f'Corrigindo livro {book.id} - {book.titulo} (ID externo: {external_id})')

                # Definir novas URLs de capa
                new_url = f'https://books.google.com/books/content?id={external_id}&printsec=frontcover&img=1&zoom=0&source=gbs_api'
                book.capa_url = new_url

                # Corrigir dados externos
                if hasattr(book, 'external_data') and book.external_data:
                    try:
                        data = json.loads(book.external_data)

                        # Adicionar imageLinks se não existir
                        if 'volumeInfo' in data and 'imageLinks' not in data['volumeInfo']:
                            data['volumeInfo']['imageLinks'] = {
                                'thumbnail': f'https://books.google.com/books/content?id={external_id}&printsec=frontcover&img=1&zoom=1&source=gbs_api',
                                'small': f'https://books.google.com/books/content?id={external_id}&printsec=frontcover&img=1&zoom=2&source=gbs_api',
                                'medium': f'https://books.google.com/books/content?id={external_id}&printsec=frontcover&img=1&zoom=3&source=gbs_api',
                            }
                            book.external_data = json.dumps(data)
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'  Erro ao corrigir dados externos: {str(e)}'))

                # Salvar as alterações
                book.save()
                self.stdout.write(self.style.SUCCESS(f'  Livro corrigido com URL: {new_url}'))

        # Verificar livros sem URL de capa
        books_without_cover = Book.objects.filter(Q(capa_url='') | Q(capa_url__isnull=True))
        self.stdout.write(f'Encontrados {books_without_cover.count()} livros sem URL de capa')

        for book in books_without_cover:
            # Se tem external_id, criar URL padrão
            if book.external_id:
                new_url = f'https://books.google.com/books/content?id={book.external_id}&printsec=frontcover&img=1&zoom=0&source=gbs_api'
                book.capa_url = new_url
                book.save(update_fields=['capa_url'])
                self.stdout.write(f'  Adicionada URL para livro {book.id} - {book.titulo}: {new_url}')

    def download_missing_covers(self, force=False):
        """Baixa capas para livros que precisam"""
        self.stdout.write(self.style.WARNING('Baixando capas de livros...'))

        # Obter diretório para salvar as capas
        media_root = settings.MEDIA_ROOT
        covers_dir = os.path.join(media_root, 'livros', 'capas', 'downloads')

        # Criar diretório se não existir
        os.makedirs(covers_dir, exist_ok=True)

        # Livros para verificar
        if force:
            books = Book.objects.all()
            self.stdout.write(f'Verificando todos os {books.count()} livros (modo força)')
        else:
            books = Book.objects.filter(
                Q(capa_url__startswith='https://books.google.com') |
                Q(external_id__in=['rC2eswEACAAJ', 'sFE4nwEACAAJ'])
            )
            self.stdout.write(f'Verificando {books.count()} livros do Google Books')

        download_count = 0
        for book in books:
            if not book.capa_url:
                continue

            # Verificar se queremos baixar esta imagem
            if force or 'books.google.com' in book.capa_url or book.external_id in ['rC2eswEACAAJ', 'sFE4nwEACAAJ']:
                # Nome do arquivo a ser salvo
                file_name = f"downloaded_{book.external_id or book.id}.jpg"
                file_path = os.path.join(covers_dir, file_name)

                # Se já existe, pular (a menos que force esteja ativado)
                if os.path.exists(file_path) and not force:
                    continue

                # Baixar a imagem
                try:
                    # Tentar diferentes URLs
                    urls_to_try = [
                        book.capa_url,
                        book.capa_url.replace('zoom=1', 'zoom=0'),
                        book.capa_url.replace('zoom=1', 'zoom=2'),
                        f'https://books.google.com/books/content?id={book.external_id}&printsec=frontcover&img=1&zoom=0&source=gbs_api',
                        f'https://books.google.com/books/publisher/content/images/frontcover/{book.external_id}?fife=w400-h600'
                    ]

                    # Adicionar headers para evitar bloqueios
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
                        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
                        'Referer': 'https://books.google.com/',
                    }

                    success = False
                    for url in urls_to_try:
                        if not url:
                            continue

                        try:
                            response = requests.get(url, headers=headers, timeout=10)

                            if response.status_code == 200 and response.headers.get('Content-Type', '').startswith(
                                    'image/'):
                                # Verificar se é uma imagem válida
                                try:
                                    img = Image.open(BytesIO(response.content))
                                    img.verify()  # Verifica se é uma imagem válida

                                    # Salvar a imagem
                                    with open(file_path, 'wb') as f:
                                        f.write(response.content)

                                    # Atualizar URL da capa
                                    relative_path = os.path.join('livros', 'capas', 'downloads', file_name)
                                    book.capa_url = '/' + os.path.join('media', relative_path)
                                    book.save(update_fields=['capa_url'])

                                    self.stdout.write(
                                        self.style.SUCCESS(f'  Baixada capa para livro {book.id} - {book.titulo}'))
                                    download_count += 1
                                    success = True
                                    break
                                except Exception:
                                    # Não é uma imagem válida, continuar para o próximo URL
                                    continue
                        except requests.RequestException:
                            # Erro na requisição, continuar para o próximo URL
                            continue

                        # Pausa breve para evitar sobrecarga
                        time.sleep(0.2)

                    if not success:
                        self.stdout.write(
                            self.style.WARNING(f'  Não foi possível baixar capa para livro {book.id} - {book.titulo}'))

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  Erro ao baixar capa para livro {book.id}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS(f'Baixadas {download_count} capas de livros'))

    def verify_all_books(self, force=False):
        """Verifica todos os livros para garantir que têm capas válidas"""
        self.stdout.write(self.style.WARNING('Verificando todos os livros...'))

        # Verificar todos os livros ou apenas os potencialmente problemáticos
        if force:
            books = Book.objects.all()
        else:
            # Livros do Google Books ou com IDs problemáticos
            books = Book.objects.filter(
                Q(capa_url__contains='books.google.com') |
                Q(external_id__in=['rC2eswEACAAJ', 'sFE4nwEACAAJ'])
            )

        self.stdout.write(f'Verificando {books.count()} livros')

        no_cover_count = 0
        for book in books:
            if not book.capa_url:
                no_cover_count += 1
                self.stdout.write(self.style.WARNING(f'  Livro sem capa: {book.id} - {book.titulo}'))

                # Se tem ID externo, adicionar URL de fallback
                if book.external_id:
                    fallback_url = f'https://books.google.com/books/content?id={book.external_id}&printsec=frontcover&img=1&zoom=0&source=gbs_api'
                    book.capa_url = fallback_url
                    book.save(update_fields=['capa_url'])
                    self.stdout.write(self.style.SUCCESS(f'    Adicionada URL de fallback: {fallback_url}'))
                else:
                    self.stdout.write(
                        self.style.ERROR(f'    Não foi possível adicionar URL de fallback (sem ID externo)'))

        self.stdout.write(self.style.SUCCESS(f'Verificação concluída. {no_cover_count} livros sem capa.'))
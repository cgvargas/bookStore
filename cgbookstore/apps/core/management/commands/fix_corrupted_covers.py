import os
import requests
from pathlib import Path
from PIL import Image
from django.core.management.base import BaseCommand
from django.conf import settings
from cgbookstore.apps.core.models.book import Book


class Command(BaseCommand):
    help = 'Detecta e corrige imagens de capas corrompidas ou placeholders'

    def add_arguments(self, parser):
        parser.add_argument(
            '--min-size',
            type=int,
            default=15000,
            help='Tamanho mínimo em bytes para considerar imagem válida (default: 15KB)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas reporta problemas sem fazer correções'
        )
        parser.add_argument(
            '--fix-all',
            action='store_true',
            help='Corrige todos os problemas encontrados automaticamente'
        )
        parser.add_argument(
            '--external-id',
            type=str,
            help='Corrigir livro específico pelo external_id'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('\n=== DETECTOR DE CAPAS CORROMPIDAS ===\n')
        )

        min_size = options['min_size']
        dry_run = options['dry_run']
        fix_all = options['fix_all']
        external_id = options['external_id']

        self.stdout.write(f'🔍 Tamanho mínimo: {min_size} bytes')
        self.stdout.write(f'🔧 Modo: {"DRY RUN" if dry_run else "CORREÇÃO ATIVA"}')

        if external_id:
            self._fix_specific_book(external_id, min_size, dry_run)
        else:
            self._scan_all_covers(min_size, dry_run, fix_all)

    def _fix_specific_book(self, external_id, min_size, dry_run):
        """Corrige livro específico"""
        try:
            book = Book.objects.get(external_id=external_id)
            self.stdout.write(f'\n📖 ANALISANDO: {book.titulo} (ID: {book.id})')

            if self._analyze_book_cover(book, min_size, dry_run, force_fix=True):
                self.stdout.write(self.style.SUCCESS('✅ Livro corrigido com sucesso!'))
            else:
                self.stdout.write(self.style.WARNING('⚠️ Não foi possível corrigir automaticamente'))

        except Book.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Livro não encontrado: {external_id}'))

    def _scan_all_covers(self, min_size, dry_run, fix_all):
        """Escaneia todas as capas em busca de problemas"""
        self.stdout.write('\n🔍 ESCANEANDO CAPAS...\n')

        # Buscar livros com capas locais
        books_with_covers = Book.objects.filter(
            capa_url__icontains='downloaded_'
        ).exclude(capa_url__isnull=True).exclude(capa_url='')

        self.stdout.write(f'📊 Encontrados {books_with_covers.count()} livros com capas locais')

        corrupted_count = 0
        fixed_count = 0

        for book in books_with_covers:
            if self._is_cover_corrupted(book, min_size):
                corrupted_count += 1
                self.stdout.write(f'\n❌ CORRUPTED: {book.titulo} (ID: {book.id})')
                self.stdout.write(f'   External ID: {book.external_id}')
                self.stdout.write(f'   Capa URL: {book.capa_url}')

                if not dry_run and (fix_all or self._should_fix_book(book)):
                    if self._analyze_book_cover(book, min_size, dry_run=False, force_fix=True):
                        fixed_count += 1
                        self.stdout.write(self.style.SUCCESS('   ✅ Corrigido!'))
                    else:
                        self.stdout.write(self.style.WARNING('   ⚠️ Falha na correção'))

        self.stdout.write(f'\n📊 RESUMO:')
        self.stdout.write(f'   Capas corrompidas encontradas: {corrupted_count}')
        if not dry_run:
            self.stdout.write(f'   Capas corrigidas: {fixed_count}')

    def _is_cover_corrupted(self, book, min_size):
        """Verifica se a capa está corrompida"""
        if not book.capa_url:
            return False

        # Construir path do arquivo
        media_root = getattr(settings, 'MEDIA_ROOT', '')
        if not media_root:
            return False

        # Normalizar path
        file_path = book.capa_url.replace('\\', '/').replace('/media/', '')
        full_path = Path(media_root) / file_path

        if not full_path.exists():
            return True  # Arquivo não existe = corrompido

        # Verificar tamanho
        file_size = full_path.stat().st_size
        if file_size < min_size:
            return True  # Muito pequeno = suspeito

        # Tentar abrir como imagem
        try:
            with Image.open(full_path) as img:
                img.verify()  # Verifica se é imagem válida
            return False  # Imagem válida
        except Exception:
            return True  # Não é imagem válida = corrompido

    def _analyze_book_cover(self, book, min_size, dry_run, force_fix=False):
        """Analisa e corrige capa de um livro"""
        if dry_run and not force_fix:
            return False

        self.stdout.write(f'🔧 Corrigindo: {book.titulo}')

        # 1. Deletar arquivo corrompido se existir
        self._delete_corrupted_file(book)

        # 2. Tentar redownload se tiver external_id
        if book.external_id:
            if self._redownload_from_api(book):
                return True

        # 3. Usar imagem fallback
        self._set_fallback_image(book)
        return True

    def _delete_corrupted_file(self, book):
        """Deleta arquivo corrompido"""
        try:
            media_root = getattr(settings, 'MEDIA_ROOT', '')
            if not media_root or not book.capa_url:
                return

            file_path = book.capa_url.replace('\\', '/').replace('/media/', '')
            full_path = Path(media_root) / file_path

            if full_path.exists():
                full_path.unlink()
                self.stdout.write(f'   🗑️ Arquivo corrompido deletado: {file_path}')

        except Exception as e:
            self.stdout.write(f'   ⚠️ Erro ao deletar: {e}')

    def _redownload_from_api(self, book):
        """Tenta redownload da API Google Books"""
        try:
            self.stdout.write(f'   📥 Tentando redownload da API...')

            # Buscar dados na API Google Books
            api_url = f'https://www.googleapis.com/books/v1/volumes/{book.external_id}'
            response = requests.get(api_url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                volume_info = data.get('volumeInfo', {})
                image_links = volume_info.get('imageLinks', {})

                # Tentar diferentes tamanhos de imagem
                image_urls = [
                    image_links.get('extraLarge'),
                    image_links.get('large'),
                    image_links.get('medium'),
                    image_links.get('small'),
                    image_links.get('thumbnail')
                ]

                for image_url in image_urls:
                    if image_url:
                        # Converter HTTP para HTTPS
                        if image_url.startswith('http://'):
                            image_url = image_url.replace('http://', 'https://')

                        if self._download_image(book, image_url):
                            return True

        except Exception as e:
            self.stdout.write(f'   ❌ Erro na API: {e}')

        return False

    def _download_image(self, book, image_url):
        """Baixa imagem de uma URL"""
        try:
            self.stdout.write(f'   📥 Baixando: {image_url[:60]}...')

            response = requests.get(image_url, timeout=15, stream=True)
            if response.status_code == 200:
                # Verificar content-type
                content_type = response.headers.get('content-type', '')
                if 'image' not in content_type.lower():
                    self.stdout.write(f'   ❌ Content-Type inválido: {content_type}')
                    return False

                # Construir path de destino
                media_root = getattr(settings, 'MEDIA_ROOT', '')
                downloads_dir = Path(media_root) / 'livros' / 'capas' / 'downloads'
                downloads_dir.mkdir(parents=True, exist_ok=True)

                filename = f'downloaded_{book.external_id}.jpg'
                file_path = downloads_dir / filename

                # Salvar arquivo
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                # Verificar se a imagem é válida
                try:
                    with Image.open(file_path) as img:
                        img.verify()

                    # Verificar tamanho
                    file_size = file_path.stat().st_size
                    if file_size > 10000:  # > 10KB
                        # Atualizar banco
                        book.capa_url = f'/media/livros/capas/downloads/{filename}'
                        book.save(update_fields=['capa_url'])

                        self.stdout.write(f'   ✅ Download bem-sucedido ({file_size} bytes)')
                        return True
                    else:
                        file_path.unlink()  # Deletar se muito pequeno
                        self.stdout.write(f'   ❌ Imagem muito pequena ({file_size} bytes)')

                except Exception:
                    file_path.unlink()  # Deletar se inválida
                    self.stdout.write(f'   ❌ Imagem inválida')

        except Exception as e:
            self.stdout.write(f'   ❌ Erro no download: {e}')

        return False

    def _set_fallback_image(self, book):
        """Define imagem de fallback"""
        self.stdout.write(f'   🔄 Usando imagem fallback')

        # Limpar capa_url para usar fallback no template
        book.capa_url = ''
        book.save(update_fields=['capa_url'])

    def _should_fix_book(self, book):
        """Pergunta se deve corrigir o livro (modo interativo)"""
        while True:
            response = input(f'\n   Corrigir "{book.titulo}"? (s/n/a=all): ').lower().strip()
            if response in ['s', 'y', 'sim', 'yes']:
                return True
            elif response in ['n', 'não', 'no']:
                return False
            elif response in ['a', 'all', 'todos']:
                return True
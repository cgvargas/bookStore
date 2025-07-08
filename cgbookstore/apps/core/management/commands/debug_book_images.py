import os
import requests
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse
from cgbookstore.apps.core.models.book import Book


class Command(BaseCommand):
    help = 'Diagnostica problemas com arquivos de imagem de livros e configurações de media'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-http',
            action='store_true',
            help='Testa acesso HTTP às imagens'
        )
        parser.add_argument(
            '--book-id',
            type=str,
            help='Testa livro específico pelo ID'
        )
        parser.add_argument(
            '--external-id',
            type=str,
            help='Testa livro específico pelo external_id'
        )
        parser.add_argument(
            '--fix-paths',
            action='store_true',
            help='Tenta corrigir paths com barras incorretas'
        )
        parser.add_argument(
            '--sample-size',
            type=int,
            default=10,
            help='Número de livros para testar (default: 10)'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('\n=== DIAGNÓSTICO DE IMAGENS DE LIVROS ===\n')
        )

        # Verificar configurações Django
        self._check_django_media_settings()

        # Analisar livro específico se solicitado
        if options['book_id']:
            self._analyze_specific_book(options['book_id'], 'id', options)
        elif options['external_id']:
            self._analyze_specific_book(options['external_id'], 'external_id', options)
        else:
            # Analisar amostra de livros
            self._analyze_sample_books(options)

    def _check_django_media_settings(self):
        """Verifica configurações de media do Django"""
        self.stdout.write('⚙️  CONFIGURAÇÕES DJANGO MEDIA:\n')

        # MEDIA_ROOT
        media_root = getattr(settings, 'MEDIA_ROOT', 'NÃO CONFIGURADO')
        self.stdout.write(f'   MEDIA_ROOT: {media_root}')

        if media_root != 'NÃO CONFIGURADO':
            media_path = Path(media_root)
            exists = media_path.exists()
            is_dir = media_path.is_dir() if exists else False
            writable = os.access(media_path, os.W_OK) if exists else False

            self.stdout.write(
                f'   Existe: {"✅" if exists else "❌"} | Diretório: {"✅" if is_dir else "❌"} | Gravável: {"✅" if writable else "❌"}')

        # MEDIA_URL
        media_url = getattr(settings, 'MEDIA_URL', 'NÃO CONFIGURADO')
        self.stdout.write(f'   MEDIA_URL: {media_url}')

        # DEBUG
        debug_mode = getattr(settings, 'DEBUG', False)
        self.stdout.write(f'   DEBUG: {debug_mode}')

        if debug_mode:
            self.stdout.write('   ℹ️  Modo DEBUG ativo - Django serve arquivos media automaticamente')
        else:
            self.stdout.write('   ⚠️  Modo PRODUÇÃO - Servidor web deve servir arquivos media')

        # Verificar diretório de capas
        if media_root != 'NÃO CONFIGURADO':
            covers_path = Path(media_root) / 'livros' / 'capas' / 'downloads'
            self.stdout.write(f'   Diretório de capas: {covers_path}')

            if covers_path.exists():
                files_count = len(list(covers_path.glob('*')))
                self.stdout.write(f'   Arquivos no diretório: {files_count}')

                # Listar alguns arquivos
                if files_count > 0:
                    sample_files = list(covers_path.glob('*.jpg'))[:5]
                    self.stdout.write('   Exemplos de arquivos:')
                    for file in sample_files:
                        size = file.stat().st_size if file.exists() else 0
                        self.stdout.write(f'     • {file.name} ({size} bytes)')
            else:
                self.stdout.write('   ❌ Diretório de capas não existe')

        self.stdout.write('')

    def _analyze_specific_book(self, book_identifier, id_type, options):
        """Analisa livro específico"""
        self.stdout.write(f'🎯 ANALISANDO LIVRO ESPECÍFICO ({id_type.upper()}: {book_identifier})\n')

        try:
            if id_type == 'id':
                book = Book.objects.get(id=book_identifier)
            else:
                book = Book.objects.get(external_id=book_identifier)

            self._analyze_book_image(book, options)

        except Book.DoesNotExist:
            self.stdout.write(f'❌ Livro não encontrado: {id_type}={book_identifier}')
        except Exception as e:
            self.stdout.write(f'❌ Erro ao buscar livro: {e}')

    def _analyze_sample_books(self, options):
        """Analisa amostra de livros com imagens locais"""
        self.stdout.write(f'📊 ANALISANDO AMOSTRA DE LIVROS:\n')

        # Buscar livros com capas locais (downloaded_)
        books_with_local_covers = Book.objects.filter(
            capa_url__icontains='downloaded_'
        )[:options['sample_size']]

        if not books_with_local_covers.exists():
            # Buscar livros com capas em /media
            books_with_local_covers = Book.objects.filter(
                capa_url__icontains='/media'
            )[:options['sample_size']]

        if not books_with_local_covers.exists():
            self.stdout.write('❌ Nenhum livro encontrado com capas locais')

            # Mostrar alguns livros para debug
            sample_books = Book.objects.all()[:5]
            self.stdout.write('\n📋 Amostra de livros no banco:')
            for book in sample_books:
                self.stdout.write(f'   ID: {book.id} | Título: {book.titulo[:50]} | Capa: {book.capa_url}')
            return

        self.stdout.write(f'Encontrados {books_with_local_covers.count()} livros com capas locais\n')

        # Analisar cada livro
        for i, book in enumerate(books_with_local_covers, 1):
            self.stdout.write(f'📖 LIVRO {i}/{len(books_with_local_covers)}:')
            self._analyze_book_image(book, options)
            self.stdout.write('')

    def _analyze_book_image(self, book, options):
        """Analisa imagem de um livro específico"""
        self.stdout.write(f'   ID: {book.id}')
        self.stdout.write(f'   Título: {book.titulo}')
        self.stdout.write(f'   External ID: {book.external_id}')
        self.stdout.write(f'   Capa URL: {book.capa_url}')

        if not book.capa_url:
            self.stdout.write('   ❌ Sem URL de capa definida')
            return

        # Normalizar path (corrigir barras)
        normalized_path = book.capa_url.replace('\\', '/')
        if normalized_path != book.capa_url:
            self.stdout.write(f'   ⚠️  Path com barras incorretas detectado')
            self.stdout.write(f'   Path normalizado: {normalized_path}')

            if options.get('fix_paths'):
                book.capa_url = normalized_path
                book.save(update_fields=['capa_url'])
                self.stdout.write('   ✅ Path corrigido no banco de dados')

        # Verificar se é path local
        if book.capa_url.startswith('/media') or 'livros/capas' in book.capa_url:
            self._check_local_file(book.capa_url, options)
        elif book.capa_url.startswith('http'):
            self._check_remote_file(book.capa_url, options)
        else:
            self.stdout.write(f'   ❓ Tipo de URL não reconhecido: {book.capa_url}')

    def _check_local_file(self, file_path, options):
        """Verifica arquivo local"""
        self.stdout.write('   📁 ARQUIVO LOCAL:')

        # Construir path completo
        media_root = getattr(settings, 'MEDIA_ROOT', '')

        if file_path.startswith('/media'):
            # Remover /media do início
            relative_path = file_path[7:] if file_path.startswith('/media/') else file_path[6:]
        else:
            relative_path = file_path

        full_path = Path(media_root) / relative_path
        self.stdout.write(f'     Path completo: {full_path}')

        # Verificar existência
        if full_path.exists():
            file_size = full_path.stat().st_size
            self.stdout.write(f'     ✅ Arquivo existe ({file_size} bytes)')

            # Verificar se não está vazio
            if file_size == 0:
                self.stdout.write('     ❌ Arquivo vazio!')
            elif file_size < 1024:
                self.stdout.write(f'     ⚠️  Arquivo muito pequeno ({file_size} bytes)')

            # Verificar permissões
            readable = os.access(full_path, os.R_OK)
            self.stdout.write(f'     Legível: {"✅" if readable else "❌"}')

        else:
            self.stdout.write('     ❌ Arquivo não existe')

            # Verificar se diretório pai existe
            parent_dir = full_path.parent
            if parent_dir.exists():
                self.stdout.write(f'     Diretório pai existe: {parent_dir}')

                # Listar arquivos similares
                similar_files = list(parent_dir.glob(f'*{full_path.stem}*'))
                if similar_files:
                    self.stdout.write('     Arquivos similares encontrados:')
                    for similar in similar_files[:3]:
                        self.stdout.write(f'       • {similar.name}')
            else:
                self.stdout.write(f'     ❌ Diretório pai não existe: {parent_dir}')

        # Testar URL HTTP se solicitado
        if options.get('test_http'):
            self._test_http_access(file_path, 'local')

    def _check_remote_file(self, url, options):
        """Verifica arquivo remoto"""
        self.stdout.write('   🌐 ARQUIVO REMOTO:')
        self.stdout.write(f'     URL: {url}')

        if options.get('test_http'):
            self._test_http_access(url, 'remote')

    def _test_http_access(self, url_or_path, file_type):
        """Testa acesso HTTP à imagem"""
        self.stdout.write(f'   🔗 TESTE HTTP ({file_type.upper()}):')

        try:
            # Construir URL completa para arquivos locais
            if file_type == 'local':
                base_url = 'http://127.0.0.1:8000'  # URL padrão do Django dev server
                if not url_or_path.startswith('/'):
                    url_or_path = '/' + url_or_path
                test_url = base_url + url_or_path
            else:
                test_url = url_or_path

            self.stdout.write(f'     Testando: {test_url}')

            response = requests.head(test_url, timeout=10, allow_redirects=True)

            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', 'N/A')
                content_length = response.headers.get('Content-Length', 'N/A')
                self.stdout.write(f'     ✅ Acessível (Status: {response.status_code})')
                self.stdout.write(f'     Content-Type: {content_type}')
                self.stdout.write(f'     Content-Length: {content_length}')

                # Verificar se é realmente uma imagem
                if 'image' not in content_type.lower():
                    self.stdout.write(f'     ⚠️  Content-Type não é imagem!')

            elif response.status_code == 404:
                self.stdout.write(f'     ❌ Não encontrado (404)')
            elif response.status_code == 403:
                self.stdout.write(f'     ❌ Sem permissão (403)')
            elif response.status_code == 500:
                self.stdout.write(f'     ❌ Erro do servidor (500)')
            else:
                self.stdout.write(f'     ❌ Status: {response.status_code}')

        except requests.exceptions.ConnectionError:
            self.stdout.write(f'     ❌ Erro de conexão - Servidor pode estar offline')
        except requests.exceptions.Timeout:
            self.stdout.write(f'     ❌ Timeout - Servidor não respondeu')
        except requests.exceptions.RequestException as e:
            self.stdout.write(f'     ❌ Erro na requisição: {e}')
        except Exception as e:
            self.stdout.write(f'     ❌ Erro inesperado: {e}')

    def _format_file_size(self, size_bytes):
        """Formata tamanho do arquivo em formato legível"""
        if size_bytes < 1024:
            return f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
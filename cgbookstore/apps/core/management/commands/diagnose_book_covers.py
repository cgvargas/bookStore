import re
import json
import urllib.parse
from django.core.management.base import BaseCommand
from django.db import connection
from cgbookstore.apps.core.models.book import Book


class Command(BaseCommand):
    help = 'Diagnostica problemas com capas de livros específicas'

    def add_arguments(self, parser):
        parser.add_argument('--fix', action='store_true', help='Tenta corrigir os problemas identificados')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando diagnóstico de capas de livros...'))

        # 1. Verificar livros com IDs externos específicos
        problematic_ids = ['5y04AwAAQBAJ', 'rC2eswEACAAJ']
        self.stdout.write(self.style.WARNING(f'Buscando livros com IDs problemáticos conhecidos: {problematic_ids}'))

        for book_id in problematic_ids:
            books = Book.objects.filter(external_id=book_id)
            if books.exists():
                self.stdout.write(self.style.SUCCESS(f'Encontrado livro com ID {book_id}:'))
                for book in books:
                    self._analyze_book(book, options.get('fix', False))
            else:
                self.stdout.write(self.style.WARNING(f'Nenhum livro encontrado com ID {book_id}'))

        # 2. Verificar URLs de capas com padrões problemáticos
        self.stdout.write(self.style.WARNING('Buscando livros com URLs de capa potencialmente problemáticas...'))

        # Livros com URLs do Google Books
        books_with_google = Book.objects.filter(capa_url__icontains='books.google.com')
        self.stdout.write(
            self.style.SUCCESS(f'Encontrados {books_with_google.count()} livros com URLs do Google Books'))

        for book in books_with_google:
            self._analyze_book(book, options.get('fix', False))

        # 3. Verificar livros com external_data
        self.stdout.write(self.style.WARNING('Buscando livros com dados externos...'))

        # Consulta SQL raw para encontrar livros com external_data não vazio
        # Isso é útil se external_data não for um campo indexado
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id FROM core_book 
                WHERE external_data IS NOT NULL 
                AND external_data != '' 
                LIMIT 100
            """)
            book_ids = [row[0] for row in cursor.fetchall()]

        books_with_data = Book.objects.filter(id__in=book_ids)
        self.stdout.write(self.style.SUCCESS(f'Encontrados {len(book_ids)} livros com dados externos'))

        for book in books_with_data:
            self._analyze_book(book, options.get('fix', False))

        # 4. Resumir os resultados
        self.stdout.write(self.style.SUCCESS('Diagnóstico concluído.'))

    def _analyze_book(self, book, fix=False):
        """Analisa um livro específico para problemas de capa"""
        self.stdout.write(f'  ID: {book.id}, Título: {book.titulo}')
        self.stdout.write(f'  ID Externo: {book.external_id}')
        self.stdout.write(f'  URL da Capa: {book.capa_url}')

        # Analisar URL da capa
        capa_url = book.capa_url or ''
        if 'books.google.com' in capa_url or 'googleusercontent.com' in capa_url:
            # Verificar problemas comuns
            if capa_url.startswith('http://'):
                self.stdout.write(self.style.ERROR('    Problema: URL usa HTTP em vez de HTTPS'))
                if fix:
                    book.capa_url = capa_url.replace('http://', 'https://')
                    book.save(update_fields=['capa_url'])
                    self.stdout.write(self.style.SUCCESS('    Corrigido: URL atualizada para HTTPS'))

            # Verificar se a URL está completa
            if 'printsec' not in capa_url and 'zoom' not in capa_url:
                self.stdout.write(self.style.ERROR('    Problema: URL não contém parâmetros necessários'))
                if fix:
                    # Extrair ID do livro e criar URL padronizada
                    id_match = re.search(r'[?&]id=([^&]+)', capa_url)
                    if id_match:
                        book_id = id_match.group(1)
                        new_url = f"https://books.google.com/books/content?id={book_id}&printsec=frontcover&img=1&zoom=1&source=gbs_api"
                        book.capa_url = new_url
                        book.save(update_fields=['capa_url'])
                        self.stdout.write(self.style.SUCCESS(f'    Corrigido: URL padronizada para {new_url}'))

        # Analisar dados externos
        if hasattr(book, 'external_data') and book.external_data:
            self.stdout.write('  Dados Externos: Presentes')
            try:
                external_data = json.loads(book.external_data)

                # Verificar estrutura dos dados externos
                if 'volumeInfo' in external_data:
                    vol_info = external_data['volumeInfo']

                    # Verificar links de imagem
                    if 'imageLinks' in vol_info:
                        self.stdout.write(f"    Links de Imagem: {', '.join(vol_info['imageLinks'].keys())}")

                        # Verificar URL de thumbnail
                        if 'thumbnail' in vol_info['imageLinks']:
                            thumbnail = vol_info['imageLinks']['thumbnail']
                            self.stdout.write(f'    Thumbnail: {thumbnail}')

                            # Verificar problemas com thumbnail
                            if thumbnail.startswith('http://'):
                                self.stdout.write(self.style.ERROR('    Problema: Thumbnail usa HTTP'))
                                if fix:
                                    vol_info['imageLinks']['thumbnail'] = thumbnail.replace('http://', 'https://')
                                    book.external_data = json.dumps(external_data)
                                    book.save(update_fields=['external_data'])
                                    self.stdout.write(
                                        self.style.SUCCESS('    Corrigido: Thumbnail atualizado para HTTPS'))
                    else:
                        self.stdout.write(self.style.ERROR('    Problema: Sem imageLinks em volumeInfo'))
                else:
                    self.stdout.write(self.style.ERROR('    Problema: Sem volumeInfo nos dados externos'))

                # Verificar ID nos dados externos
                if 'id' in external_data:
                    ext_id = external_data['id']
                    self.stdout.write(f'    ID nos dados externos: {ext_id}')

                    # Verificar consistência de ID
                    if book.external_id and book.external_id != ext_id:
                        self.stdout.write(self.style.ERROR(
                            f'    Problema: ID externo inconsistente ({book.external_id} vs {ext_id})'))
                        if fix:
                            book.external_id = ext_id
                            book.save(update_fields=['external_id'])
                            self.stdout.write(self.style.SUCCESS(f'    Corrigido: ID externo atualizado para {ext_id}'))
            except json.JSONDecodeError:
                self.stdout.write(self.style.ERROR('    Problema: Dados externos não são JSON válido'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    Erro ao analisar dados externos: {str(e)}'))

        self.stdout.write('')  # Linha em branco para separar
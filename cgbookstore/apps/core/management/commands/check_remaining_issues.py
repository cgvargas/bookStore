import json
import base64
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.core.cache import caches
from cgbookstore.apps.core.models.book import Book


class Command(BaseCommand):
    help = 'Verifica e corrige livros com problemas restantes'

    def add_arguments(self, parser):
        parser.add_argument('--fix', action='store_true', help='Corrige o problema automaticamente')

    def handle(self, *args, **options):
        fix = options.get('fix', False)

        self.stdout.write(self.style.SUCCESS('Verificando livros com problemas restantes...'))

        # 1. Verificar livros com URLs problemáticas
        problem_books = []

        # Verificar livros com empty string ou null em capa_url
        books_empty_url = Book.objects.filter(Q(capa_url='') | Q(capa_url__isnull=True))
        self.stdout.write(self.style.WARNING(f'Encontrados {books_empty_url.count()} livros sem URL de capa'))

        for book in books_empty_url:
            problem_books.append(book)
            self.stdout.write(f'Livro sem URL: ID {book.id}, Título: {book.titulo}, ID Externo: {book.external_id}')

            # Se tem external_data, verificar se há imageLinks
            if hasattr(book, 'external_data') and book.external_data:
                try:
                    data = json.loads(book.external_data)
                    if 'volumeInfo' in data:
                        vol_info = data['volumeInfo']
                        if 'imageLinks' not in vol_info:
                            self.stdout.write(self.style.ERROR('  Problema: Sem imageLinks em volumeInfo'))

                            # Se tem ID externo, tentar gerar URL de capa padrão
                            if book.external_id and fix:
                                new_url = f'https://books.google.com/books/content?id={book.external_id}&printsec=frontcover&img=1&zoom=1&source=gbs_api'
                                book.capa_url = new_url
                                book.save(update_fields=['capa_url'])
                                self.stdout.write(self.style.SUCCESS(f'  Corrigido: Adicionada URL {new_url}'))
                        elif 'thumbnail' in vol_info.get('imageLinks', {}):
                            thumbnail = vol_info['imageLinks']['thumbnail']
                            if not book.capa_url and fix:
                                # Usa o thumbnail como capa_url
                                thumbnail_https = thumbnail.replace('http://', 'https://')
                                book.capa_url = thumbnail_https
                                book.save(update_fields=['capa_url'])
                                self.stdout.write(self.style.SUCCESS(f'  Corrigido: Adicionada URL {thumbnail_https}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  Erro ao processar dados externos: {str(e)}'))

        # 2. Verificar casos específicos conhecidos
        specific_ids = ['rC2eswEACAAJ', 'sFE4nwEACAAJ']  # IDs problemáticos conhecidos
        for ext_id in specific_ids:
            books = Book.objects.filter(external_id=ext_id)

            for book in books:
                self.stdout.write(
                    f'Verificando livro específico: ID {book.id}, Título: {book.titulo}, ID Externo: {book.external_id}')

                if not book.capa_url and fix:
                    # Para estes IDs específicos, usar uma URL alternativa
                    new_url = f'https://books.google.com/books/content?id={book.external_id}&printsec=frontcover&img=1&zoom=0&source=gbs_api'
                    book.capa_url = new_url
                    book.save(update_fields=['capa_url'])
                    self.stdout.write(self.style.SUCCESS(f'  Corrigido: Adicionada URL {new_url}'))

                # Tentar corrigir dados externos
                if hasattr(book, 'external_data') and book.external_data:
                    try:
                        data = json.loads(book.external_data)
                        modified = False

                        # Se não tem imageLinks, adicionar
                        if 'volumeInfo' in data and 'imageLinks' not in data['volumeInfo'] and fix:
                            data['volumeInfo']['imageLinks'] = {
                                'thumbnail': f'https://books.google.com/books/content?id={book.external_id}&printsec=frontcover&img=1&zoom=1&source=gbs_api',
                                'small': f'https://books.google.com/books/content?id={book.external_id}&printsec=frontcover&img=1&zoom=2&source=gbs_api',
                                'medium': f'https://books.google.com/books/content?id={book.external_id}&printsec=frontcover&img=1&zoom=3&source=gbs_api',
                            }
                            modified = True
                            self.stdout.write(
                                self.style.SUCCESS('  Corrigido: Adicionados imageLinks aos dados externos'))

                        if modified and fix:
                            book.external_data = json.dumps(data)
                            book.save(update_fields=['external_data'])
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'  Erro ao processar dados externos: {str(e)}'))

        # 3. Limpar caches relacionados
        if fix:
            self.stdout.write(self.style.WARNING('Limpando caches...'))

            cache_names = ['image_proxy', 'google_books', 'books_recommendations']
            for cache_name in cache_names:
                try:
                    caches[cache_name].clear()
                    self.stdout.write(self.style.SUCCESS(f'Cache "{cache_name}" limpo com sucesso'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Erro ao limpar cache "{cache_name}": {str(e)}'))

        self.stdout.write(self.style.SUCCESS('Verificação concluída!'))
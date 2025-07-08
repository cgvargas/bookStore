import json
from django.core.management.base import BaseCommand
from django.core.cache import caches
from cgbookstore.apps.core.models.book import Book


class Command(BaseCommand):
    help = 'Corrige URLs de capas de livros do Google Books'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Apenas simula as alterações sem salvar')

    def handle(self, *args, **options):
        dry_run = options.get('dry-run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('Modo de simulação ativado - nenhuma alteração será salva!'))

        self.stdout.write(self.style.SUCCESS('Iniciando correção de capas de livros...'))

        # 1. Corrigir URLs de capa no campo capa_url
        self.stdout.write(self.style.WARNING('Corrigindo URLs de capa...'))

        books_with_http = Book.objects.filter(capa_url__startswith='http://')
        self.stdout.write(self.style.SUCCESS(f'Encontrados {books_with_http.count()} livros com URLs HTTP'))

        updated_count = 0
        for book in books_with_http:
            if book.capa_url.startswith('http://'):
                self.stdout.write(f'Livro ID {book.id}: {book.titulo}')
                self.stdout.write(f'  URL antiga: {book.capa_url}')

                new_url = book.capa_url.replace('http://', 'https://')
                self.stdout.write(f'  URL nova: {new_url}')

                if not dry_run:
                    book.capa_url = new_url
                    book.save(update_fields=['capa_url'])
                    updated_count += 1

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f'Atualizadas {updated_count} URLs de capa'))

        # 2. Corrigir thumbnails em dados externos
        self.stdout.write(self.style.WARNING('Corrigindo thumbnails em dados externos...'))

        # Encontrar livros com dados externos que contêm "http://"
        books_with_external_data = Book.objects.exclude(external_data__isnull=True).exclude(external_data='')
        self.stdout.write(
            self.style.SUCCESS(f'Verificando {books_with_external_data.count()} livros com dados externos'))

        external_updated_count = 0
        for book in books_with_external_data:
            try:
                if book.external_data and 'http://' in book.external_data:
                    data = json.loads(book.external_data)
                    has_changes = False

                    # Verificar e atualizar links de imagem
                    if 'volumeInfo' in data and 'imageLinks' in data['volumeInfo']:
                        for key, url in data['volumeInfo']['imageLinks'].items():
                            if isinstance(url, str) and url.startswith('http://'):
                                self.stdout.write(f'Livro ID {book.id}: {book.titulo}')
                                self.stdout.write(f'  {key} antigo: {url}')

                                data['volumeInfo']['imageLinks'][key] = url.replace('http://', 'https://')
                                self.stdout.write(f'  {key} novo: {data["volumeInfo"]["imageLinks"][key]}')
                                has_changes = True

                    if has_changes and not dry_run:
                        book.external_data = json.dumps(data)
                        book.save(update_fields=['external_data'])
                        external_updated_count += 1

            except (json.JSONDecodeError, TypeError, AttributeError) as e:
                self.stdout.write(self.style.ERROR(f'Erro ao processar dados externos do livro {book.id}: {str(e)}'))

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f'Atualizados {external_updated_count} dados externos'))

        # 3. Limpar caches relacionados
        if not dry_run:
            self.stdout.write(self.style.WARNING('Limpando caches...'))

            # Limpar cache de imagens
            cache_names = ['image_proxy', 'google_books', 'books_recommendations']
            for cache_name in cache_names:
                try:
                    caches[cache_name].clear()
                    self.stdout.write(self.style.SUCCESS(f'Cache "{cache_name}" limpo com sucesso'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Erro ao limpar cache "{cache_name}": {str(e)}'))

        self.stdout.write(self.style.SUCCESS('Processo de correção concluído!'))
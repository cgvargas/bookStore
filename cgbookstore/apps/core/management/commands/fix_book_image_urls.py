# cgbookstore/apps/core/management/commands/fix_book_image_urls.py
import logging
import re
from django.core.management.base import BaseCommand
from cgbookstore.apps.core.models.book import Book
from django.db.models import Q

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Corrige URLs de capas de livros do Google Books armazenadas no banco de dados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa em modo de simulação sem fazer alterações reais',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força atualização mesmo para URLs que parecem boas',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        force_update = options.get('force', False)

        try:
            # Encontrar livros com URLs do Google Books
            google_books_urls = Book.objects.filter(
                Q(capa_url__icontains='books.google.com') |
                Q(capa_url__icontains='googleusercontent.com')
            )

            self.stdout.write(
                self.style.SUCCESS(f'Encontrados {google_books_urls.count()} livros com URLs do Google Books'))

            # Contadores para estatísticas
            updated_count = 0
            failed_count = 0
            skipped_count = 0

            # Processar cada livro
            for book in google_books_urls:
                original_url = book.capa_url

                # Verificar se a URL já inclui parâmetros importantes e não estamos forçando atualização
                if not force_update and self.check_url_quality(original_url):
                    self.stdout.write(f'Ignorando livro ID {book.id} ({book.titulo}) - URL já tem boa qualidade')
                    skipped_count += 1
                    continue

                # Normalizar a URL
                try:
                    new_url = self.normalize_google_books_url(original_url)

                    if original_url != new_url or force_update:
                        self.stdout.write(f'Atualizando livro ID {book.id}: {book.titulo}')
                        self.stdout.write(f'   URL Antiga: {original_url}')
                        self.stdout.write(f'   URL Nova:   {new_url}')

                        if not dry_run:
                            book.capa_url = new_url
                            book.save(update_fields=['capa_url'])

                        updated_count += 1
                    else:
                        self.stdout.write(f'Nenhuma mudança necessária para livro ID {book.id} ({book.titulo})')
                        skipped_count += 1

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Erro ao processar livro ID {book.id}: {str(e)}'))
                    failed_count += 1

            # Relatório final
            if dry_run:
                self.stdout.write(self.style.WARNING('MODO DE SIMULAÇÃO - Nenhuma alteração foi feita'))

            self.stdout.write(self.style.SUCCESS(
                f'Processamento concluído: {updated_count} atualizados, '
                f'{skipped_count} ignorados, {failed_count} falhas'
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro durante a execução: {str(e)}'))
            logger.error(f'Erro na correção de URLs: {str(e)}')

    def check_url_quality(self, url):
        """Verifica se a URL já contém parâmetros de qualidade"""
        if not url:
            return False

        # Verificar parâmetros importantes
        has_zoom = 'zoom=' in url
        has_img = 'img=' in url
        has_source = 'source=' in url

        # Verificar se tem tokens que podem expirar (isso é negativo)
        has_imgtk = 'imgtk=' in url

        # Se já tem alguns parâmetros importantes e não tem tokens que expiram
        return has_zoom and has_img and has_source and not has_imgtk

    def normalize_google_books_url(self, url):
        """Normaliza URLs do Google Books para formato mais estável"""
        if not url:
            return url

        # Extrair o ID do livro, que é a parte mais importante
        id_match = re.search(r'id=([^&]+)', url)
        if not id_match:
            return url  # Não conseguimos identificar o ID, manter original

        book_id = id_match.group(1)

        # Reconstruir URL completamente para garantir formato consistente
        new_url = f"https://books.google.com/books/content?id={book_id}&printsec=frontcover&img=1&zoom=1&source=gbs_api"

        # Verificar se a URL original tinha edge=curl e adicionar se necessário
        if 'edge=curl' in url:
            new_url += '&edge=curl'

        return new_url
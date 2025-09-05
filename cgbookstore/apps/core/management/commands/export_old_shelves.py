import json
from django.core.management.base import BaseCommand
from cgbookstore.apps.core.models import BookShelfSection


class Command(BaseCommand):
    help = 'Exporta os dados das prateleiras antigas para um arquivo JSON.'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando exportação de prateleiras antigas...")
        data = []
        old_shelves = BookShelfSection.objects.all().select_related('section', 'shelf_type')

        for shelf in old_shelves:
            shelf_data = {
                'section_id': shelf.section.id,
                'max_books': shelf.max_livros,
                'manual_books': list(shelf.bookshelfitem_set.order_by('ordem').values_list('livro_id', flat=True)),
                'automatic_filter_field': shelf.shelf_type.filtro_campo if shelf.shelf_type else None,
                'automatic_filter_value': shelf.shelf_type.filtro_valor if shelf.shelf_type else None,
            }
            data.append(shelf_data)
            self.stdout.write(f"  - Exportando prateleira '{shelf.section.titulo}'")

        with open('old_shelves_backup.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        self.stdout.write(
            self.style.SUCCESS(f"Sucesso! {len(data)} prateleiras exportadas para old_shelves_backup.json"))
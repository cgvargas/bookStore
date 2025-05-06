from django.core.management.base import BaseCommand
from cgbookstore.apps.core.models import Achievement


class Command(BaseCommand):
    help = 'Cria conquistas padrão no sistema'

    def handle(self, *args, **options):
        # Lista de conquistas padrão
        achievements = [
            {
                'code': 'first_book',
                'name': 'Primeiro Livro',
                'description': 'Adicionou seu primeiro livro à prateleira',
                'icon': 'bi-book',
                'category': 'reading',
                'tier': 'bronze',
                'points': 10,
                'is_secret': False
            },
            {
                'code': 'book_collector_i',
                'name': 'Colecionador I',
                'description': 'Adicionou 5 livros às prateleiras',
                'icon': 'bi-bookshelf',
                'category': 'collection',
                'tier': 'bronze',
                'points': 20,
                'is_secret': False
            },
            {
                'code': 'book_collector_ii',
                'name': 'Colecionador II',
                'description': 'Adicionou 25 livros às prateleiras',
                'icon': 'bi-bookshelf',
                'category': 'collection',
                'tier': 'silver',
                'points': 40,
                'is_secret': False
            },
            {
                'code': 'bookworm_i',
                'name': 'Devorador de Livros I',
                'description': 'Leu 5 livros',
                'icon': 'bi-eyeglasses',
                'category': 'reading',
                'tier': 'bronze',
                'points': 30,
                'is_secret': False
            },
            {
                'code': 'bookworm_ii',
                'name': 'Devorador de Livros II',
                'description': 'Leu 15 livros',
                'icon': 'bi-eyeglasses',
                'category': 'reading',
                'tier': 'silver',
                'points': 50,
                'is_secret': False
            },
            {
                'code': 'explorer_i',
                'name': 'Explorador I',
                'description': 'Visitou 10 páginas de detalhes de livros',
                'icon': 'bi-compass',
                'category': 'exploration',
                'tier': 'bronze',
                'points': 15,
                'is_secret': False
            },
            {
                'code': 'loyal_reader',
                'name': 'Leitor Leal',
                'description': 'Membro por mais de 30 dias',
                'icon': 'bi-calendar-check',
                'category': 'special',
                'tier': 'bronze',
                'points': 25,
                'is_secret': False
            },
            {
                'code': 'genre_explorer',
                'name': 'Explorador de Gêneros',
                'description': 'Leu livros de pelo menos 3 gêneros diferentes',
                'icon': 'bi-tags',
                'category': 'exploration',
                'tier': 'silver',
                'points': 35,
                'is_secret': False
            }
        ]

        # Criar as conquistas
        created = 0
        updated = 0
        for achievement_data in achievements:
            obj, created_flag = Achievement.objects.get_or_create(
                code=achievement_data['code'],
                defaults=achievement_data
            )
            if created_flag:
                created += 1
            else:
                # Atualizar campos existentes
                for key, value in achievement_data.items():
                    setattr(obj, key, value)
                obj.save()
                updated += 1

        self.stdout.write(self.style.SUCCESS(f'Criadas {created} e atualizadas {updated} conquistas'))
from django.core.management.base import BaseCommand
from cgbookstore.apps.core.models.home_content import DefaultShelfType

class Command(BaseCommand):
    help = 'Cria os tipos de prateleiras padrão'

    def handle(self, *args, **kwargs):
        shelves = [
            {
                'nome': 'Lançamentos',
                'identificador': 'lancamentos',
                'filtro_campo': 'e_lancamento',
                'filtro_valor': 'True',
                'ordem': 1
            },
            {
                'nome': 'Destaques',
                'identificador': 'destaques',
                'filtro_campo': 'e_destaque',
                'filtro_valor': 'True',
                'ordem': 2
            },
            {
                'nome': 'Mais Vendidos',
                'identificador': 'mais_vendidos',
                'filtro_campo': 'quantidade_vendida',
                'filtro_valor': 'True',
                'ordem': 3
            },
            {
                'nome': 'Adaptados para Filmes e Séries',
                'identificador': 'filmes_series',
                'filtro_campo': 'adaptado_filme',
                'filtro_valor': 'True',
                'ordem': 4
            },
            {
                'nome': 'Mangás',
                'identificador': 'mangas',
                'filtro_campo': 'e_manga',
                'filtro_valor': 'True',
                'ordem': 5
            }
        ]

        for shelf in shelves:
            DefaultShelfType.objects.get_or_create(
                identificador=shelf['identificador'],
                defaults=shelf
            )
            self.stdout.write(
                self.style.SUCCESS(f'Prateleira {shelf["nome"]} criada/atualizada com sucesso!')
            )
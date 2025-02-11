# Arquivo: cgbookstore/apps/core/recommendations/analytics/management/commands/generate_test_data.py

from django.core.management.base import BaseCommand
from cgbookstore.apps.core.recommendations.analytics.tests.generate_test_data import create_test_data

class Command(BaseCommand):
    help = 'Gera dados de teste para o dashboard de recomendações'

    def handle(self, *args, **kwargs):
        try:
            create_test_data()
            self.stdout.write(self.style.SUCCESS('Dados de teste gerados com sucesso!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao gerar dados de teste: {str(e)}'))
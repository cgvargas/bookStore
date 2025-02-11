# Arquivo: cgbookstore/apps/core/recommendations/analytics/management/commands/clean_test_data.py

from django.core.management.base import BaseCommand
from cgbookstore.apps.core.recommendations.analytics.models import RecommendationInteraction
from cgbookstore.apps.core.models.book import Book
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Remove todos os dados de teste do sistema'

    def handle(self, *args, **kwargs):
        try:
            # Remove interações de teste
            RecommendationInteraction.objects.filter(
                book__titulo__startswith='Livro Teste'
            ).delete()

            # Remove livros de teste
            Book.objects.filter(titulo__startswith='Livro Teste').delete()

            # Remove usuários de teste
            User = get_user_model()
            User.objects.filter(username__startswith='test_user_').delete()

            self.stdout.write(self.style.SUCCESS('Dados de teste removidos com sucesso!'))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao remover dados de teste: {str(e)}')
            )
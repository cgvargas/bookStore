from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from cgbookstore.apps.core.models import Profile

User = get_user_model()


class Command(BaseCommand):
    help = 'Cria perfis para usuários existentes que não possuem'

    def handle(self, *args, **kwargs):
        users = User.objects.all()
        count = 0
        for user in users:
            profile, created = Profile.objects.get_or_create(user=user)
            if created:
                count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Criados {count} novos perfis')
        )
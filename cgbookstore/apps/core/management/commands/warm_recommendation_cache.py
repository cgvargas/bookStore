# cgbookstore/apps/core/management/commands/warm_recommendation_cache.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from cgbookstore.apps.core.recommendations.utils.cache_manager import RecommendationCache
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Pré-aquece o cache de recomendações para usuários ativos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='ID específico do usuário para aquecer cache'
        )
        parser.add_argument(
            '--active-days',
            type=int,
            default=30,
            help='Considerar usuários ativos nos últimos X dias'
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        active_days = options.get('active_days')

        if user_id:
            # Aquece cache para usuário específico
            try:
                user = User.objects.get(id=user_id)
                self.stdout.write(f"Aquecendo cache para usuário {user.username}...")
                RecommendationCache.warm_cache(user)
                self.stdout.write(self.style.SUCCESS(f"Cache aquecido para {user.username}"))
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Usuário com ID {user_id} não encontrado"))
        else:
            # Aquece cache para usuários ativos
            from django.utils import timezone
            from datetime import timedelta

            cutoff_date = timezone.now() - timedelta(days=active_days)

            # Busca usuários com atividade recente
            active_users = User.objects.filter(
                bookshelves__updated_at__gte=cutoff_date
            ).distinct()

            self.stdout.write(f"Encontrados {active_users.count()} usuários ativos")

            for user in active_users:
                try:
                    self.stdout.write(f"Aquecendo cache para {user.username}...")
                    RecommendationCache.warm_cache(user)
                    self.stdout.write(self.style.SUCCESS(f"✓ {user.username}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"✗ {user.username}: {str(e)}"))

            self.stdout.write(self.style.SUCCESS("\nCache aquecido para todos os usuários ativos!"))
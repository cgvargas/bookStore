# cgbookstore/apps/core/recommendations/signals.py

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
import logging

from ..models import UserBookShelf, Book, Profile
from .utils.cache_manager import RecommendationCache

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=UserBookShelf)
def invalidate_cache_on_shelf_save(sender, instance, created, **kwargs):
    """Invalida cache quando um livro é adicionado ou modificado na prateleira"""
    try:
        if created:
            # Novo livro adicionado
            event = 'book_added'
        else:
            # Prateleira modificada
            event = 'shelf_changed'

        RecommendationCache.invalidate_user_cache(instance.user, event)

        # Se o livro foi marcado como lido, invalida perfil de idioma
        if instance.shelf_type == 'lido':
            RecommendationCache.invalidate_user_cache(instance.user, 'reading_completed')

        logger.info(f"Cache invalidado para usuário {instance.user.id} - evento: {event}")

    except Exception as e:
        logger.error(f"Erro ao invalidar cache no signal: {str(e)}")


@receiver(post_delete, sender=UserBookShelf)
def invalidate_cache_on_shelf_delete(sender, instance, **kwargs):
    """Invalida cache quando um livro é removido da prateleira"""
    try:
        RecommendationCache.invalidate_user_cache(instance.user, 'book_removed')
        logger.info(f"Cache invalidado para usuário {instance.user.id} - livro removido")

    except Exception as e:
        logger.error(f"Erro ao invalidar cache no signal: {str(e)}")


@receiver(pre_save, sender=UserBookShelf)
def track_shelf_changes(sender, instance, **kwargs):
    """Rastreia mudanças no tipo de prateleira"""
    if instance.pk:
        try:
            old_instance = UserBookShelf.objects.get(pk=instance.pk)
            if old_instance.shelf_type != instance.shelf_type:
                # Tipo de prateleira mudou
                instance._shelf_type_changed = True
        except UserBookShelf.DoesNotExist:
            pass


@receiver(post_save, sender=Profile)
def invalidate_cache_on_profile_update(sender, instance, created, **kwargs):
    """Invalida cache quando perfil do usuário é atualizado"""
    try:
        if not created:  # Apenas em atualizações
            RecommendationCache.invalidate_user_cache(instance.user, 'preference_updated')
            logger.info(f"Cache invalidado para usuário {instance.user.id} - perfil atualizado")
    except Exception as e:
        logger.error(f"Erro ao invalidar cache no signal de perfil: {str(e)}")


@receiver(post_save, sender='core.ReadingStats')
def invalidate_cache_on_stats_update(sender, instance, **kwargs):
    """Invalida cache quando estatísticas de leitura são atualizadas"""
    try:
        RecommendationCache.invalidate_user_cache(instance.user, 'behavior')
        logger.info(f"Cache de comportamento invalidado para usuário {instance.user.id}")
    except Exception as e:
        logger.error(f"Erro ao invalidar cache de estatísticas: {str(e)}")


@receiver(post_save, sender='core.ReadingProgress')
def update_reading_velocity(sender, instance, created, **kwargs):
    """Atualiza velocidade de leitura quando progresso é atualizado"""
    try:
        if instance.is_active:
            # Poderíamos calcular velocidade de leitura aqui
            # e invalidar cache se mudou significativamente
            pass
    except Exception as e:
        logger.error(f"Erro ao processar progresso de leitura: {str(e)}")
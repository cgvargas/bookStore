# Arquivo: cgbookstore/apps/core/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Profile, UserBookShelf


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Cria um perfil automaticamente quando um novo usuário é criado.
    """
    if created:
        Profile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Garante que o perfil do usuário seja salvo.
    """
    # Usar get_or_create é mais seguro do que a lógica anterior
    Profile.objects.get_or_create(user=instance)

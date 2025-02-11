# cgbookstore/apps/core/signals.py
"""
Módulo de sinais (signals) para o aplicativo core.

Gerencia criação automática de perfis de usuário após registro.
Utiliza sinais do Django para sincronizar criação e salvamento
de perfis de usuário.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Profile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Cria um perfil automaticamente quando um novo usuário é criado.

    Características:
    - Disparado após salvamento de um novo usuário
    - Garante que cada usuário tenha um perfil associado

    Args:
        sender: Modelo que disparou o sinal (User)
        instance: Instância do usuário criado
        created: Booleano indicando se o usuário foi criado
        **kwargs: Argumentos adicionais do sinal
    """
    if created:
        # Cria um novo perfil associado ao usuário recem-criado
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Garante que o perfil do usuário seja salvo.

    Características:
    - Disparado após salvamento de um usuário
    - Cria perfil se não existir
    - Salva perfil associado

    Args:
        sender: Modelo que disparou o sinal (User)
        instance: Instância do usuário
        **kwargs: Argumentos adicionais do sinal
    """
    # Verifica se o usuário já possui um perfil
    if not hasattr(instance, 'profile'):
        # Cria perfil se não existir
        Profile.objects.create(user=instance)

    # Salva o perfil do usuário
    instance.profile.save()
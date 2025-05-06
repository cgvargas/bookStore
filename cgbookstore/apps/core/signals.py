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
from django.utils import timezone
from datetime import timedelta

from .models import UserBookShelf, UserAchievement, Achievement, ReadingStats


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


@receiver(post_save, sender=UserBookShelf)
def check_achievements(sender, instance, created, **kwargs):
    """
    Verifica e atribui conquistas quando um livro é adicionado a uma prateleira.
    """
    if not created:
        return  # Só verifica em novas adições

    user = instance.user

    # Verificar conquista de primeiro livro
    user_books_count = UserBookShelf.objects.filter(user=user).count()
    if user_books_count == 1:
        achievement = Achievement.objects.filter(code='first_book').first()
        if achievement:
            UserAchievement.objects.get_or_create(
                user=user,
                achievement=achievement
            )

    # Verificar conquista de colecionador
    if user_books_count == 5:
        achievement = Achievement.objects.filter(code='book_collector_i').first()
        if achievement:
            UserAchievement.objects.get_or_create(
                user=user,
                achievement=achievement
            )

    if user_books_count == 25:
        achievement = Achievement.objects.filter(code='book_collector_ii').first()
        if achievement:
            UserAchievement.objects.get_or_create(
                user=user,
                achievement=achievement
            )

    # Verificar conquistas relacionadas a livros lidos
    if instance.shelf_type == 'lido':
        books_read = UserBookShelf.objects.filter(user=user, shelf_type='lido').count()

        if books_read == 5:
            achievement = Achievement.objects.filter(code='bookworm_i').first()
            if achievement:
                UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement
                )

        if books_read == 15:
            achievement = Achievement.objects.filter(code='bookworm_ii').first()
            if achievement:
                UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement
                )

        # Verificar conquista de explorador de gêneros
        genre_achievement = Achievement.objects.filter(code='genre_explorer').first()
        if genre_achievement:
            # Obter gêneros distintos dos livros lidos
            genres = UserBookShelf.objects.filter(
                user=user,
                shelf_type='lido'
            ).select_related('book').values_list('book__genero', flat=True).distinct()

            # Filtrando gêneros não vazios
            distinct_genres = [g for g in genres if g]

            if len(distinct_genres) >= 3:
                UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=genre_achievement
                )

    # Atualizar estatísticas
    stats, _ = ReadingStats.objects.get_or_create(user=user)
    stats.update_stats()
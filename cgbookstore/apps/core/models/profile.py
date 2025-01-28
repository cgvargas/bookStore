# cgbookstore/apps/core/models/profile.py

from django.db import models
from django.conf import settings


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    interests = models.TextField(max_length=500, blank=True)
    social_links = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Novas configurações de estilo do card
    def default_card_style():
        return {
            'background_color': '#ffffff',
            'text_color': '#000000',
            'border_color': '#dee2e6',
            'border_radius': '0.5rem',
            'image_style': 'circle',
            'hover_effect': 'translate',
            'icon_style': 'default'
        }

    card_style = models.JSONField(
        default=default_card_style,
        blank=True
    )

    def __str__(self):
        return f"{self.user.username}'s profile"

    def get_card_style(self):
        default_style = {
            'background_color': '#ffffff',
            'text_color': '#000000',
            'border_color': '#dee2e6',
            'border_radius': '0.5rem',
            'image_style': 'circle',
            'hover_effect': 'translate',
            'icon_style': 'default'
        }
        return {**default_style, **self.card_style}
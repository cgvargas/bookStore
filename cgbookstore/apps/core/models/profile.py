# cgbookstore/apps/core/models/profile.py
import logging
import math
from collections import Counter

from django.db import models
from django.conf import settings
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

logger = logging.getLogger(__name__)

def get_default_card_style():
    return {
        'background_color': '#ffffff',
        'text_color': '#000000',
        'border_color': '#dee2e6',
        'border_radius': '0.5rem',
        'image_style': 'circle',
        'hover_effect': 'translate',
        'icon_style': 'default'
    }


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name='Avatar')
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    interests = models.TextField(max_length=500, blank=True)
    social_links = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    favorite_quote = models.TextField(max_length=500, blank=True, verbose_name='Citação Favorita')
    favorite_quote_author = models.CharField(max_length=100, blank=True, verbose_name='Autor da Citação')
    favorite_quote_source = models.CharField(max_length=200, blank=True, verbose_name='Fonte da Citação')

    # Novas configurações de estilo do card
    def default_card_style(self):
        return get_default_card_style()

    card_style = models.JSONField(
        default=get_default_card_style,
        blank=True
    )

    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfis'

    def __str__(self):
        return f"{self.user.username}'s profile"

    def get_card_style(self):
        default_style = get_default_card_style()
        return {**default_style, **self.card_style}


class Achievement(models.Model):
    """
    Modelo para definir conquistas disponíveis no sistema.

    Cada conquista representa uma meta ou marco que os usuários podem alcançar,
    como ler certo número de livros, completar desafios, etc.
    """
    CATEGORY_CHOICES = [
        ('reading', 'Leitura'),
        ('collection', 'Coleção'),
        ('social', 'Social'),
        ('exploration', 'Exploração'),
        ('special', 'Especial')
    ]

    TIER_CHOICES = [
        ('bronze', 'Bronze'),
        ('silver', 'Prata'),
        ('gold', 'Ouro'),
        ('platinum', 'Platina')
    ]

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100, verbose_name='Nome')
    description = models.TextField(verbose_name='Descrição')
    icon = models.CharField(max_length=50, help_text="Classe do ícone Bootstrap (ex: 'bi-book')")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name='Categoria')
    tier = models.CharField(max_length=10, choices=TIER_CHOICES, default='bronze', verbose_name='Nível')
    points = models.IntegerField(default=10, verbose_name='Pontos')
    requirement = models.JSONField(default=dict, blank=True, verbose_name='Requisitos')
    is_secret = models.BooleanField(default=False, verbose_name='Secreto')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Conquista'
        verbose_name_plural = 'Conquistas'
        ordering = ['category', 'tier', 'points']

    def __str__(self):
        return f"{self.name} ({self.get_tier_display()})"


class UserAchievement(models.Model):
    """
    Modelo para registrar conquistas obtidas por usuários.

    Relaciona usuários com conquistas, registrando a data de obtenção
    e informações adicionais sobre como a conquista foi alcançada.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Usuário')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, verbose_name='Conquista')
    achieved_at = models.DateTimeField(auto_now_add=True, verbose_name='Data de Conquista')
    progress_data = models.JSONField(default=dict, blank=True, verbose_name='Dados de Progresso')

    class Meta:
        verbose_name = 'Conquista do Usuário'
        verbose_name_plural = 'Conquistas dos Usuários'
        unique_together = ('user', 'achievement')
        ordering = ['-achieved_at']

    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"


class ReadingStats(models.Model):
    """
    Modelo para armazenar estatísticas de leitura dos usuários.

    Mantém contadores e métricas sobre os hábitos de leitura,
    permitindo análises e geração de relatórios personalizados.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Usuário')
    total_books_read = models.IntegerField(default=0, verbose_name='Total de Livros Lidos')
    total_pages_read = models.IntegerField(default=0, verbose_name='Total de Páginas Lidas')
    reading_streak = models.IntegerField(default=0, verbose_name='Sequência Atual')  # Dias consecutivos de leitura
    longest_streak = models.IntegerField(default=0, verbose_name='Maior Sequência')
    favorite_genre = models.CharField(max_length=50, blank=True, verbose_name='Gênero Favorito')
    reading_velocity = models.FloatField(default=0.0, verbose_name='Velocidade de Leitura')  # Páginas por dia (média)
    books_by_month = models.JSONField(default=dict, blank=True, verbose_name='Livros por Mês')
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Estatísticas de Leitura'
        verbose_name_plural = 'Estatísticas de Leitura'

    def __str__(self):
        return f"Estatísticas de {self.user.username}"

    def calculate_reading_velocity(self):
        """
        Calcula a velocidade média de leitura em páginas por dia.
        Retorna 0 se não houver dados suficientes.
        """
        if not self.total_pages_read or not self.total_books_read:
            return 0.0

        # Calcular com base nos livros lidos nos últimos 90 dias
        # Lógica a ser implementada
        return round(self.total_pages_read / max(self.total_books_read, 1), 1)

    def update_stats(self):
        """
        Atualiza todas as estatísticas do usuário com base nos seus livros.
        Versão completamente reescrita com tratamento robusto.
        """
        import logging
        import ast
        from collections import Counter
        from .book import UserBookShelf

        logger = logging.getLogger(__name__)

        # ===== 1. Contadores Básicos =====
        read_shelves = UserBookShelf.objects.filter(user=self.user, shelf_type='lido').select_related('book')
        self.total_books_read = read_shelves.count()
        self.total_pages_read = read_shelves.aggregate(total=Sum('book__numero_paginas'))['total'] or 0

        # ===== 2. Cálculo de Livros por Mês =====
        monthly_counts = (
            read_shelves
            .annotate(month=TruncMonth('updated_at'))
            .values('month')
            .annotate(count=models.Count('id'))
            .order_by('month')
        )

        books_by_month_data = {}
        for entry in monthly_counts:
            year_str = str(entry['month'].year)
            month_str = str(entry['month'].month)
            if year_str not in books_by_month_data:
                books_by_month_data[year_str] = {str(m): 0 for m in range(1, 13)}
            books_by_month_data[year_str][month_str] = entry['count']

        self.books_by_month = books_by_month_data

        # ===== 4. Cálculo do Gênero Favorito =====

        # Usar a lógica que funciona no teste manual
        raw_data = list(read_shelves.values_list('book__genero', flat=True))

        # Se gêneros vazios, usar categoria
        if not any(item.strip() for item in raw_data if item):
            raw_data = list(read_shelves.values_list('book__categoria', flat=True))

        # Aplicar limpeza de dados corrompidos
        cleaned_genres = []
        for item in raw_data:
            if not item or not item.strip():
                continue

            # Tratar strings de lista corrompidas
            if item.startswith("['") and item.endswith("']"):
                try:
                    parsed_list = ast.literal_eval(item)
                    if isinstance(parsed_list, list) and parsed_list:
                        item = parsed_list[0]
                except (ValueError, SyntaxError):
                    pass

            # Normalizar
            normalized_item = item.strip().title()
            if normalized_item:
                cleaned_genres.append(normalized_item)

        # Calcular mais comum
        if cleaned_genres:
            genre_counts = Counter(cleaned_genres)
            most_common = genre_counts.most_common(1)
            self.favorite_genre = most_common[0][0] if most_common else "Não definido"
        else:
            self.favorite_genre = "Não definido"

        # Debug log
        logger.info(f"Estatísticas para {self.user.username}: "
                    f"Livros: {self.total_books_read}, "
                    f"Páginas: {self.total_pages_read}, "
                    f"Gênero: '{self.favorite_genre}'")

        # Salvar no banco
        self.save()


class ReadingProgress(models.Model):
    """
    Modelo para rastrear o progresso de leitura de um livro.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reading_progress')
    book = models.ForeignKey('Book', on_delete=models.CASCADE, related_name='reading_progress')
    started_at = models.DateTimeField(null=True, blank=True)
    current_page = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)  # Novo campo
    last_read_at = models.DateTimeField(auto_now=True)  # Para saber qual foi lido mais recentemente

    class Meta:
        unique_together = ('user', 'book')
        verbose_name = 'Progresso de Leitura'
        verbose_name_plural = 'Progressos de Leitura'

    def save(self, *args, **kwargs):
        # Garantir que last_read_at seja atualizado sempre que o progresso for salvo
        self.last_read_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.book.titulo} ({self.current_page} páginas)"

    def calculate_progress_percentage(self):
        """
        Calcula a porcentagem de progresso da leitura.
        """
        if not self.book.numero_paginas:
            return 0
        return min(round((self.current_page / self.book.numero_paginas) * 100), 100)

    def estimate_completion_date(self):
        """
        Estima a data de conclusão da leitura com base na velocidade atual.
        """
        if not self.started_at or not self.book.numero_paginas:
            return None

        # Calcular dias desde o início
        days_reading = max(1, (timezone.now() - self.started_at).days)

        # Calcular média de páginas por dia
        avg_pages_per_day = self.current_page / days_reading

        # Se a média for muito baixa, usar um valor mínimo
        if avg_pages_per_day < 1:
            avg_pages_per_day = 1

        # Calcular páginas restantes
        pages_left = self.book.numero_paginas - self.current_page

        # Estimar dias restantes
        days_left = math.ceil(pages_left / avg_pages_per_day)

        # Calcular data estimada
        return timezone.now() + timezone.timedelta(days=days_left)
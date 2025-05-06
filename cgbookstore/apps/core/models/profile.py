# cgbookstore/apps/core/models/profile.py
import math

from django.db import models
from django.conf import settings
from django.utils import timezone


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
        Atualiza as estatísticas com base nos livros atuais do usuário.
        """
        from .book import UserBookShelf  # Importação local para evitar circular imports

        # Obter livros lidos
        read_books = UserBookShelf.objects.filter(
            user=self.user,
            shelf_type='lido'
        ).select_related('book')

        # Atualizar contadores
        self.total_books_read = read_books.count()

        # Calcular total de páginas (se disponível)
        total_pages = 0
        for shelf in read_books:
            pages = getattr(shelf.book, 'paginas', 0)
            if pages and isinstance(pages, int):
                total_pages += pages

        self.total_pages_read = total_pages

        # Atualizar velocidade de leitura
        self.reading_velocity = self.calculate_reading_velocity()

        # Atualizar livros por mês
        # Este é um exemplo simplificado - a implementação real seria mais complexa
        if not self.books_by_month:
            self.books_by_month = {}

        current_year = timezone.now().year
        if str(current_year) not in self.books_by_month:
            self.books_by_month[str(current_year)] = {
                "1": 0, "2": 0, "3": 0, "4": 0,
                "5": 0, "6": 0, "7": 0, "8": 0,
                "9": 0, "10": 0, "11": 0, "12": 0
            }

        # Salvar alterações
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
# Arquivo: cgbookstore/apps/core/models/book.py

import logging
from django.db import models
from django.conf import settings
from django.core.cache import cache
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _

from ..managers.book_managers import BookManager
from ..recommendations.utils.cache_manager import RecommendationCache

logger = logging.getLogger(__name__)


class Book(models.Model):
    # --- Visibilidade e Sugestão de Usuários ---
    class Visibility(models.TextChoices):
        PUBLIC = 'public', _('Público (Aprovado)')
        PRIVATE = 'private', _('Privado (Aguardando Revisão)')

    visibility = models.CharField(
        _('Visibilidade'),
        max_length=10,
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
        db_index=True,
        help_text=_('Público: visível para todos. Privado: apenas para quem adicionou e para admins.')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='suggested_books',
        verbose_name=_('Sugerido por')
    )

    # --- Campos Bibliográficos ---
    titulo = models.CharField(_('Título'), max_length=200)
    subtitulo = models.CharField(_('Subtítulo'), max_length=200, blank=True)
    autor = models.CharField(_('Autor'), max_length=200)  # Mantido para compatibilidade
    tradutor = models.CharField(_('Tradutor'), max_length=200, blank=True)
    ilustrador = models.CharField(_('Ilustrador'), max_length=200, blank=True)
    editora = models.CharField(_('Editora'), max_length=100, blank=True)
    isbn = models.CharField(_('ISBN'), max_length=13, blank=True)
    edicao = models.CharField(_('Edição'), max_length=50, blank=True)
    data_publicacao = models.DateField(_('Data de Publicação'), null=True, blank=True)
    numero_paginas = models.IntegerField(_('Número de Páginas'), null=True, blank=True)
    idioma = models.CharField(_('Idioma'), max_length=50, blank=True)
    formato = models.CharField(_('Formato'), max_length=50, blank=True)
    dimensoes = models.CharField(_('Dimensões'), max_length=50, blank=True)
    peso = models.CharField(_('Peso'), max_length=20, blank=True)

    # --- Campos Comerciais ---
    preco = models.DecimalField(_('Preço'), max_digits=10, decimal_places=2, null=True, blank=True)
    preco_promocional = models.DecimalField(_('Preço Promocional'), max_digits=10, decimal_places=2, null=True,
                                            blank=True)

    # --- Campos de Conteúdo e Categorização ---
    categoria = models.CharField(_('Categoria'), max_length=100, blank=True)
    genero = models.CharField(_('Gênero Literário'), max_length=100, blank=True)
    descricao = models.TextField(_('Descrição'), blank=True)
    temas = models.TextField(_('Temas'), blank=True)
    personagens = models.TextField(_('Personagens Principais'), blank=True)
    enredo = models.TextField(_('Enredo'), blank=True)
    publico_alvo = models.CharField(_('Público-alvo'), max_length=100, blank=True)
    premios = models.TextField(_('Prêmios'), blank=True)
    adaptacoes = models.TextField(_('Adaptações'), blank=True)
    colecao = models.CharField(_('Coleção'), max_length=200, blank=True)
    classificacao = models.CharField(_('Classificação Indicativa'), max_length=50, blank=True)
    localizacao = models.CharField(_('Localização na Biblioteca'), max_length=100, blank=True)

    # --- Relacionamentos ---
    authors = models.ManyToManyField('Author', through='BookAuthor', related_name='books', verbose_name=_('Autores'))

    # --- Mídia ---
    capa = models.ImageField(_('Capa'), upload_to='livros/capas/', null=True, blank=True)
    capa_preview = models.ImageField(_('Preview da Capa'), upload_to='livros/capas/previews/', null=True, blank=True)
    capa_url = models.URLField(_('URL da Capa'), max_length=500, blank=True)

    # --- Integração Externa ---
    external_id = models.CharField(_('ID Externo'), max_length=100, blank=True, null=True)
    is_temporary = models.BooleanField(_('É Temporário'), default=False)
    external_data = models.JSONField(_('Dados Externos'), null=True, blank=True)
    origem = models.CharField(_('Origem'), max_length=50, default='local')

    # --- Web e Marketing ---
    website = models.URLField(_('Website'), max_length=200, blank=True)
    redes_sociais = models.JSONField(_('Redes Sociais'), default=dict, blank=True)
    citacoes = models.TextField(_('Citações'), blank=True)
    curiosidades = models.TextField(_('Curiosidades'), blank=True)

    # --- Auditoria e Flags ---
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)
    ativo = models.BooleanField(_('Ativo'), default=True, help_text=_('Indica se o livro está disponível no site.'))

    # --- Exibição na Home e Métricas ---
    e_lancamento = models.BooleanField(_('É lançamento'), default=False)
    e_destaque = models.BooleanField(_('Em destaque'), default=False)
    adaptado_filme = models.BooleanField(_('Filme/Série'), default=False)
    e_manga = models.BooleanField(_('É manga'), default=False)
    ordem_exibicao = models.IntegerField(_('Ordem de exibição'), default=0)

    # NOVO CAMPO DE AVALIAÇÃO
    avaliacao_media = models.DecimalField(
        _('Avaliação Média'),
        max_digits=3,
        decimal_places=2,
        default=0.0,
        null=True,
        blank=True,
        help_text=_('Avaliação média do livro (de 0 a 5), preenchida manualmente.')
    )

    tipo_shelf_especial = models.CharField(_('Prateleira'), max_length=50, blank=True)
    quantidade_vendida = models.IntegerField(_('Quantidade vendida'), default=0)
    quantidade_acessos = models.IntegerField(_('Quantidade de acessos'), default=0)

    # --- Manager ---
    objects = BookManager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.pk:
            self._original_capa = self.capa

    def get_display_cover_url(self):
        """Retorna a melhor URL de capa disponível com fallback."""
        if self.capa and hasattr(self.capa, 'url'):
            return self.capa.url
        if self.capa_url:
            return self.capa_url
        return static('images/no-cover.svg')

    def get_preview_url(self):
        """Retorna URL para preview/thumbnail da capa com fallback."""
        if self.capa_preview and hasattr(self.capa_preview, 'url'):
            return self.capa_preview.url
        if self.capa and hasattr(self.capa, 'url'):
            return self.capa.url
        if self.capa_url:
            return self.capa_url
        return static('images/no-cover.svg')

    def get_capa_url(self):
        """Retorna URL para imagem da capa em alta resolução com fallback."""
        if self.capa and hasattr(self.capa, 'url'):
            return self.capa.url
        if self.capa_url:
            return self.capa_url
        return static('images/no-cover.svg')

    def get_formatted_price(self):
        try:
            from decimal import Decimal
            if self.preco is None: return None

            preco_decimal = Decimal(str(self.preco))
            valor_formatado = f'R$ {preco_decimal:.2f}'.replace('.', ',')
            valor_promocional_formatado = None

            if self.preco_promocional is not None:
                preco_promocional_decimal = Decimal(str(self.preco_promocional))
                valor_promocional_formatado = f'R$ {preco_promocional_decimal:.2f}'.replace('.', ',')

            return {
                'valor_formatado': valor_formatado,
                'valor_promocional_formatado': valor_promocional_formatado
            }
        except (TypeError, ValueError):
            return None

    def get_primary_author(self):
        author = self.bookauthor_set.filter(is_primary=True).first()
        if author:
            return author.author
        author = self.bookauthor_set.first()
        if author:
            return author.author
        return self.autor

    def __str__(self):
        if self.visibility == self.Visibility.PRIVATE:
            return f"[PENDENTE] {self.titulo} - {self.autor}"
        return f"{self.titulo} - {self.autor}"

    class Meta:
        verbose_name = _('Livro')
        verbose_name_plural = _('Livros')
        ordering = ['titulo']

    @staticmethod
    def get_shelf_special_choices():
        """
        Retorna as opções de prateleiras especiais de forma estática e com cache.
        Busca prateleiras ativas do modelo HomeSection.
        """
        cache_key = 'shelf_special_choices_v2'
        cached_choices = cache.get(cache_key)

        if cached_choices is not None:
            logger.info(f"Retornando opções de prateleiras do cache: {len(cached_choices)} opções")
            return cached_choices

        standard_choices = [
            ('', 'Nenhum'), ('lancamentos', 'Lançamentos'), ('mais_vendidos', 'Mais Vendidos'),
            ('mais_acessados', 'Mais Acessados'), ('destaques', 'Destaques'),
            ('filmes', 'Adaptados para Filme/Série'), ('mangas', 'Mangás'), ('ebooks', 'eBooks'),
        ]

        try:
            from .home_content import HomeSection

            custom_shelves = HomeSection.objects.filter(
                ativo=True, tipo='shelf', shelf_behavior='automatic'
            ).exclude(models.Q(shelf_filter_value__exact='') | models.Q(shelf_filter_value__isnull=True))

            logger.info(f"Encontradas {custom_shelves.count()} prateleiras personalizadas")

            standard_values = {choice[0] for choice in standard_choices if choice[0]}
            custom_choices = []
            for shelf in custom_shelves:
                if shelf.shelf_filter_value and shelf.shelf_filter_value not in standard_values:
                    custom_choices.append((shelf.shelf_filter_value, shelf.titulo))

            final_choices = standard_choices + custom_choices
            cache.set(cache_key, final_choices, 600)  # Cache de 10 minutos
            logger.info(f"Opções de prateleiras geradas. Total: {len(final_choices)}")
            return final_choices

        except Exception as e:
            logger.error(f"Erro crítico ao gerar opções de prateleiras: {e}", exc_info=True)
            cache.set(cache_key, standard_choices, 60)  # Cache de 1 minuto em caso de erro
            return standard_choices

    @classmethod
    def clear_shelf_choices_cache(cls):
        """Limpa o cache das opções de prateleiras especiais."""
        cache.delete('shelf_special_choices_v2')
        logger.info("Cache de opções de prateleiras ('shelf_special_choices_v2') limpo.")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class BookAuthor(models.Model):
    book = models.ForeignKey('Book', on_delete=models.CASCADE, verbose_name=_('Livro'))
    author = models.ForeignKey('Author', on_delete=models.CASCADE, verbose_name=_('Autor'))
    role = models.CharField(_('Função'), max_length=100, blank=True, help_text=_('Ex: Autor principal, Co-autor, etc.'))
    is_primary = models.BooleanField(_('Autor Principal'), default=False)
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)

    class Meta:
        verbose_name = _('Autor do Livro')
        verbose_name_plural = _('Autores dos Livros')
        unique_together = ['book', 'author']
        ordering = ['-is_primary', 'id']

    def __str__(self):
        return f"{self.author} - {self.book}"


class UserBookShelf(models.Model):
    SHELF_CHOICES = [
        ('favorito', _('Favorito')), ('lendo', _('Lendo')),
        ('vou_ler', _('Quero Ler')), ('lido', _('Lido'))
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookshelves')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='shelves')
    shelf_type = models.CharField(_('Tipo de Prateleira'), max_length=20, choices=SHELF_CHOICES)
    added_at = models.DateTimeField(_('Adicionado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)

    class Meta:
        verbose_name = _('Prateleira de Usuário')
        verbose_name_plural = _('Prateleiras de Usuários')
        ordering = ['-added_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'book', 'shelf_type'],
                condition=~models.Q(shelf_type='favorito'),
                name='unique_user_book_non_favorite'
            ),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.book.titulo} ({self.get_shelf_type_display()})"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        RecommendationCache.invalidate_user_cache(self.user)

    def delete(self, *args, **kwargs):
        user = self.user
        super().delete(*args, **kwargs)
        RecommendationCache.invalidate_user_cache(user)
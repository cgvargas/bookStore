"""
Modelo para gerir informações detalhadas de livros no sistema.
Inclui suporte para livros locais e externos/temporários da API do Google Books.
"""

from django.utils.functional import cached_property
from django.db.models.signals import post_migrate
from django.apps import apps
from pathlib import Path
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from cgbookstore.apps.core.utils.processor import process_book_cover
from cgbookstore.config import settings
from ..recommendations.utils.cache_manager import RecommendationCache
from ..managers.book_managers import BookManager

User = get_user_model()


class Book(models.Model):
    """Modelo de livro com suporte a dados locais e externos"""

    # Campos bibliográficos básicos
    titulo = models.CharField(_('Título'), max_length=200)
    subtitulo = models.CharField(_('Subtítulo'), max_length=200, blank=True)
    autor = models.CharField(_('Autor'), max_length=200) # Mantido para compatibilidade com código existente
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
    preco = models.DecimalField(_('Preço'), max_digits=10, decimal_places=2, null=True, blank=True)
    preco_promocional = models.DecimalField(_('Preço Promocional'), max_digits=10, decimal_places=2, null=True,
                                            blank=True)

    # Campos de categorização e conteúdo
    categoria = models.CharField(_('Categoria'), max_length=100, blank=True)
    genero = models.CharField(_('Gênero Literário'), max_length=100, blank=True)
    descricao = models.TextField(_('Descrição'), blank=True)
    temas = models.TextField(_('Temas'), blank=True)
    personagens = models.TextField(_('Personagens Principais'), blank=True)
    enredo = models.TextField(_('Enredo'), blank=True)
    publico_alvo = models.CharField(_('Público-alvo'), max_length=100, blank=True)

    # Relacionamento com autores
    authors = models.ManyToManyField(
        'Author',
        through='BookAuthor',
        related_name='books',
        verbose_name=_('Autores')
    )

    # Campos de metadados e conteúdo adicional
    premios = models.TextField(_('Prêmios'), blank=True)
    adaptacoes = models.TextField(_('Adaptações'), blank=True)
    colecao = models.CharField(_('Coleção'), max_length=200, blank=True)
    classificacao = models.CharField(_('Classificação Indicativa'), max_length=50, blank=True)
    localizacao = models.CharField(_('Localização na Biblioteca'), max_length=100, blank=True)

    # Campos de mídia e recursos
    capa = models.ImageField(_('Capa'), upload_to='livros/capas/', null=True, blank=True)
    capa_preview = models.ImageField(_('Preview da Capa'), upload_to='livros/capas/previews/', null=True, blank=True)
    capa_url = models.URLField(_('URL da Capa'), max_length=500, blank=True)

    # Campos para integração com API externa
    external_id = models.CharField(_('ID Externo'), max_length=100, blank=True, null=True)
    is_temporary = models.BooleanField(_('É Temporário'), default=False)
    external_data = models.JSONField(_('Dados Externos'), null=True, blank=True)
    origem = models.CharField(_('Origem'), max_length=50, default='local')

    # Campos web e marketing
    website = models.URLField(_('Website'), max_length=200, blank=True)
    redes_sociais = models.JSONField(_('Redes Sociais'), default=dict, blank=True)
    citacoes = models.TextField(_('Citações'), blank=True)
    curiosidades = models.TextField(_('Curiosidades'), blank=True)

    # Campos de auditoria
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)

    # Campos para categorização na home
    e_lancamento = models.BooleanField(_('É lançamento'), default=False)
    quantidade_vendida = models.IntegerField(_('Quantidade vendida'), default=0)
    quantidade_acessos = models.IntegerField(_('Quantidade de acessos'), default=0)
    e_destaque = models.BooleanField(_('Em destaque'), default=False)
    adaptado_filme = models.BooleanField(_('Adaptado para filme/série'), default=False)
    e_manga = models.BooleanField(_('É manga'), default=False)
    ordem_exibicao = models.IntegerField(_('Ordem de exibição'), default=0)

    SHELF_SPECIAL_CHOICES = [
        ('lancamentos', _('Lançamentos')),
        ('mais_vendidos', _('Mais Vendidos')),
        ('mais_acessados', _('Mais Acessados')),
        ('destaques', _('Destaques')),
        ('filmes', _('Adaptados para Filme/Série')),
        ('mangas', _('Mangás')),
        ('ebooks', 'eBooks'),
    ]

    tipo_shelf_especial = models.CharField(
        _('Prateleira'),
        max_length=50,
        blank=True
    )

    # Configuração do gerenciador personalizado
    objects = BookManager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.pk:
            self._original_capa = self.capa

        # Atualiza as escolhas do campo tipo_shelf_especial
        field = self._meta.get_field('tipo_shelf_especial')
        field.choices = self.get_shelf_special_choices

    def get_capa_url(self):
        """Retorna a URL da capa, considerando fontes externas e locais"""
        if self.is_temporary and self.capa_url:
            return self.capa_url
        elif self.capa and Path(settings.MEDIA_ROOT).joinpath(self.capa.name).exists():
            return self.capa.url
        return f"{settings.STATIC_URL}images/no-cover.svg"

    def get_preview_url(self):
        """Retorna a URL do preview da capa ou fallback apropriado"""
        if self.is_temporary:
            return self.get_capa_url()
        elif self.capa_preview and Path(settings.MEDIA_ROOT).joinpath(self.capa_preview.name).exists():
            return self.capa_preview.url
        return self.get_capa_url()

    def get_formatted_price(self):
        """Retorna o preço formatado do livro"""
        try:
            if self.preco is None:
                return None

            from decimal import Decimal
            preco_decimal = Decimal(str(self.preco)) if self.preco else Decimal('0')
            valor_formatado = f'R$ {preco_decimal:.2f}'.replace('.', ',')
            valor_promocional_formatado = None

            if self.preco_promocional is not None:
                preco_promocional_decimal = Decimal(str(self.preco_promocional))
                valor_promocional_formatado = f'R$ {preco_promocional_decimal:.2f}'.replace('.', ',')

            return {
                'moeda': 'BRL',
                'valor_formatado': valor_formatado,
                'valor_promocional_formatado': valor_promocional_formatado
            }
        except (TypeError, ValueError, Exception):
            return None

    def is_external(self):
        """Verifica se o livro é de origem externa"""
        return bool(self.external_id) or self.is_temporary

    def get_origem_display(self):
        """Retorna a origem do livro formatada para exibição"""
        if self.is_external():
            return 'Google Books'
        return 'Local'

    def get_primary_author(self):
        """Retorna o autor principal do livro"""
        # Tenta obter da relação de autores
        author = self.bookauthor_set.filter(is_primary=True).first()
        if author:
            return author.author

        # Tenta obter qualquer autor associado
        author = self.bookauthor_set.first()
        if author:
            return author.author

        # Fallback para o campo autor legado
        return self.autor

    def sync_author_field(self):
        """Sincroniza o campo autor legado com os autores do relacionamento"""
        author_names = [a.author.get_nome_completo() for a in self.bookauthor_set.all()]
        if author_names:
            self.autor = ", ".join(author_names)
            self.save(update_fields=['autor'])

    def __str__(self):
        return f"{self.titulo} - {self.autor}"

    class Meta:
        verbose_name = _('Livro')
        verbose_name_plural = _('Livros')
        ordering = ['titulo']

    def save(self, *args, **kwargs):
        """Processa imagens e gerencia cache ao salvar"""
        if self.pk is None:  # Novo objeto
            if self.capa:
                process_book_cover(self, self.capa.name)
            super().save(*args, **kwargs)
        else:
            # Verifica se a imagem foi alterada
            if self.capa and hasattr(self, '_original_capa') and self.capa != self._original_capa:
                process_book_cover(self, self.capa.name)
            super().save(*args, **kwargs)

    @cached_property
    def get_shelf_special_choices(self):
        """Retorna dinamicamente as opções para tipo_shelf_especial"""
        from .home_content import DefaultShelfType
        import logging

        logger = logging.getLogger(__name__)

        # Opções padrão
        standard_choices = [
            ('', 'Nenhum'),
            ('lancamentos', 'Lançamentos'),
            ('mais_vendidos', 'Mais Vendidos'),
            ('mais_acessados', 'Mais Acessados'),
            ('destaques', 'Destaques'),
            ('filmes', 'Adaptados para Filme/Série'),
            ('mangas', 'Mangás'),
            ('ebooks', 'eBooks'),
        ]

        # Adiciona tipos personalizados
        try:
            custom_shelves = DefaultShelfType.objects.filter(ativo=True)
            custom_choices = [(shelf.identificador, shelf.nome) for shelf in custom_shelves
                              if shelf.identificador not in dict(standard_choices)]
            return standard_choices + custom_choices
        except Exception as e:
            logger.error(f"Erro ao carregar tipos de prateleiras personalizados: {str(e)}")
            return standard_choices


class BookAuthor(models.Model):
    """Modelo intermediário para relacionamento entre livros e autores"""
    book = models.ForeignKey('Book', on_delete=models.CASCADE, verbose_name=_('Livro'))
    author = models.ForeignKey('Author', on_delete=models.CASCADE, verbose_name=_('Autor'))
    role = models.CharField(_('Função'), max_length=100, blank=True,
                          help_text=_('Ex: Autor principal, Co-autor, Editor, etc.'))
    is_primary = models.BooleanField(_('Autor Principal'), default=False)
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)

    class Meta:
        verbose_name = _('Autor do Livro')
        verbose_name_plural = _('Autores dos Livros')
        unique_together = ['book', 'author']  # Evita duplicação
        ordering = ['is_primary', 'id']

    def __str__(self):
        return f"{self.author} - {self.book}"

    def save(self, *args, **kwargs):
        # Se for marcado como autor principal, garante que não haja outro
        if self.is_primary:
            BookAuthor.objects.filter(book=self.book, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        # Se não houver autor principal, marca este como principal
        elif not BookAuthor.objects.filter(book=self.book, is_primary=True).exists():
            self.is_primary = True

        super().save(*args, **kwargs)

        # Sincroniza o campo autor legado
        self.book.sync_author_field()


def get_tipo_shelf_especial_choices(sender, **kwargs):
    """Atualiza as escolhas disponíveis para o campo tipo_shelf_especial"""
    Book = apps.get_model('core', 'Book')
    field = Book._meta.get_field('tipo_shelf_especial')

    # Obtém o modelo DefaultShelfType
    DefaultShelfType = apps.get_model('core', 'DefaultShelfType')

    # Opções padrão
    standard_choices = [
        ('', 'Nenhum'),
        ('lancamentos', 'Lançamentos'),
        ('mais_vendidos', 'Mais Vendidos'),
        ('mais_acessados', 'Mais Acessados'),
        ('destaques', 'Destaques'),
        ('filmes', 'Adaptados para Filme/Série'),
        ('mangas', 'Mangás'),
        ('ebooks', 'eBooks'),
    ]

    # Adiciona tipos personalizados
    try:
        custom_shelves = DefaultShelfType.objects.filter(ativo=True)
        custom_choices = [(shelf.identificador, shelf.nome) for shelf in custom_shelves
                          if shelf.identificador not in dict(standard_choices)]
        field.choices = standard_choices + custom_choices
    except Exception:
        field.choices = standard_choices


# Conector de sinal para atualização automática
post_migrate.connect(get_tipo_shelf_especial_choices)


class UserBookShelf(models.Model):
    """
    Modelo para gerenciar as prateleiras virtuais dos usuários,
    permitindo organizar livros em diferentes categorias.
    """
    SHELF_CHOICES = [
        ('favorito', _('Favorito')),
        ('lendo', _('Lendo')),
        ('vou_ler', _('Quero Ler')),
        ('lido', _('Lido'))
    ]

    # Campos de relacionamento
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookshelves')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='shelves')

    # Campos de categorização
    shelf_type = models.CharField(_('Tipo de Prateleira'), max_length=20, choices=SHELF_CHOICES)

    # Campos de auditoria
    added_at = models.DateTimeField(_('Adicionado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)

    class Meta:
        verbose_name = _('Prateleira de Usuário')
        verbose_name_plural = _('Prateleiras de Usuários')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username} - {self.book.titulo} ({self.get_shelf_type_display()})"

    @staticmethod
    def get_shelf_books(user, shelf_type, limit=8):
        """
        Retorna os livros de uma prateleira específica do usuário

        Args:
            user: Usuário
            shelf_type: Tipo de prateleira
            limit: Limite de livros (padrão: 8)
        """
        return UserBookShelf.objects.filter(
            user=user,
            shelf_type=shelf_type
        ).select_related('book')[:limit]

    def save(self, *args, **kwargs):
        """Sobrescreve o método save para invalidar cache"""
        super().save(*args, **kwargs)
        # Invalida cache de recomendações do usuário
        RecommendationCache.invalidate_user_cache(self.user)

    def delete(self, *args, **kwargs):
        """Sobrescreve o método delete para invalidar cache"""
        user = self.user  # Guarda referência ao usuário
        super().delete(*args, **kwargs)
        # Invalida cache de recomendações do usuário
        RecommendationCache.invalidate_user_cache(user)
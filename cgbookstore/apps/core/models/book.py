from pathlib import Path
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from cgbookstore.apps.core.utils.image_processor import process_book_cover
from cgbookstore.config import settings

User = get_user_model()


class Book(models.Model):
    """
    Modelo para gerenciar informações detalhadas de livros no sistema.
    Inclui dados bibliográficos, conteúdo e informações adicionais.
    """
    # Campos bibliográficos básicos
    titulo = models.CharField(_('Título'), max_length=200)
    subtitulo = models.CharField(_('Subtítulo'), max_length=200, blank=True)
    autor = models.CharField(_('Autor'), max_length=200)
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

    # Campos de categorização e conteúdo
    categoria = models.CharField(_('Categoria'), max_length=100, blank=True)
    genero = models.CharField(_('Gênero Literário'), max_length=100, blank=True)
    descricao = models.TextField(_('Descrição'), blank=True)
    temas = models.TextField(_('Temas'), blank=True)
    personagens = models.TextField(_('Personagens Principais'), blank=True)
    enredo = models.TextField(_('Enredo'), blank=True)
    publico_alvo = models.CharField(_('Público-alvo'), max_length=100, blank=True)

    # Campos de metadados e conteúdo adicional
    premios = models.TextField(_('Prêmios'), blank=True)
    adaptacoes = models.TextField(_('Adaptações'), blank=True)
    colecao = models.CharField(_('Coleção'), max_length=200, blank=True)
    classificacao = models.CharField(_('Classificação Indicativa'), max_length=50, blank=True)
    localizacao = models.CharField(_('Localização na Biblioteca'), max_length=100, blank=True)

    # Campos de mídia e recursos
    capa = models.ImageField(_('Capa'), upload_to='livros/capas/', null=True, blank=True)
    capa_preview = models.ImageField(_('Preview da Capa'), upload_to='livros/capas/previews/', null=True, blank=True)

    # Campos de conteúdo textual
    prefacio = models.TextField(_('Prefácio/Introdução'), blank=True)
    posfacio = models.TextField(_('Posfácio'), blank=True)
    notas = models.TextField(_('Notas de Rodapé'), blank=True)
    bibliografia = models.TextField(_('Bibliografia'), blank=True)
    indice = models.TextField(_('Índice'), blank=True)
    glossario = models.TextField(_('Glossário'), blank=True)
    apendices = models.TextField(_('Apêndices'), blank=True)

    # Campos web e marketing
    website = models.URLField(_('Website'), max_length=200, blank=True)
    redes_sociais = models.JSONField(_('Redes Sociais'), default=dict, blank=True)
    preco = models.JSONField(_('Preços'), default=dict, blank=True)
    citacoes = models.TextField(_('Citações'), blank=True)
    curiosidades = models.TextField(_('Curiosidades'), blank=True)

    # Campos de auditoria
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)

    def get_capa_url(self):
        """Retorna a URL da capa ou imagem padrão se não existir"""
        if self.capa and Path(settings.MEDIA_ROOT).joinpath(self.capa.name).exists():
            return self.capa.url
        return f"{settings.STATIC_URL}images/no-cover.svg"

    def get_preview_url(self):
        """Retorna a URL do preview da capa ou URL da capa como fallback"""
        if self.capa_preview and Path(settings.MEDIA_ROOT).joinpath(self.capa_preview.name).exists():
            return self.capa_preview.url
        return self.get_capa_url()

    class Meta:
        verbose_name = _('Livro')
        verbose_name_plural = _('Livros')
        ordering = ['titulo']

    def __str__(self):
        return f"{self.titulo} - {self.autor}"

    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para processar imagens antes de salvar.
        """
        if self.pk is None:  # Novo objeto
            if self.capa:
                process_book_cover(self, self.capa.name)
            super().save(*args, **kwargs)
        else:
            # Verifica se a imagem foi alterada
            if self.capa and hasattr(self, '_original_capa') and self.capa != self._original_capa:
                process_book_cover(self, self.capa.name)
            super().save(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.pk:
            self._original_capa = self.capa


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
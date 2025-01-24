from pathlib import Path
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from cgbookstore.config import settings

User = get_user_model()

class Book(models.Model):
    # Informações básicas
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

    # Conteúdo
    categoria = models.CharField(_('Categoria'), max_length=100, blank=True)
    genero = models.CharField(_('Gênero Literário'), max_length=100, blank=True)
    descricao = models.TextField(_('Descrição'), blank=True)
    temas = models.TextField(_('Temas'), blank=True)
    personagens = models.TextField(_('Personagens Principais'), blank=True)
    enredo = models.TextField(_('Enredo'), blank=True)
    publico_alvo = models.CharField(_('Público-alvo'), max_length=100, blank=True)

    # Informações adicionais
    premios = models.TextField(_('Prêmios'), blank=True)
    adaptacoes = models.TextField(_('Adaptações'), blank=True)
    colecao = models.CharField(_('Coleção'), max_length=200, blank=True)
    classificacao = models.CharField(_('Classificação Indicativa'), max_length=50, blank=True)
    localizacao = models.CharField(_('Localização na Biblioteca'), max_length=100, blank=True)
    capa = models.ImageField(_('Capa'), upload_to='livros/capas/', null=True, blank=True)
    prefacio = models.TextField(_('Prefácio/Introdução'), blank=True)
    posfacio = models.TextField(_('Posfácio'), blank=True)
    notas = models.TextField(_('Notas de Rodapé'), blank=True)
    bibliografia = models.TextField(_('Bibliografia'), blank=True)
    indice = models.TextField(_('Índice'), blank=True)
    glossario = models.TextField(_('Glossário'), blank=True)
    apendices = models.TextField(_('Apêndices'), blank=True)
    website = models.URLField(_('Website'), max_length=200, blank=True)
    redes_sociais = models.JSONField(_('Redes Sociais'), default=dict, blank=True)
    preco = models.JSONField(_('Preços'), default=dict, blank=True)
    citacoes = models.TextField(_('Citações'), blank=True)
    curiosidades = models.TextField(_('Curiosidades'), blank=True)

    # Campos de sistema
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)

    def get_capa_url(self):
        if self.capa and Path(settings.MEDIA_ROOT).joinpath(self.capa.name).exists():
            return self.capa.url
        return f"{settings.STATIC_URL}images/no-cover.svg"

    class Meta:
        verbose_name = _('Livro')
        verbose_name_plural = _('Livros')
        ordering = ['titulo']

    def __str__(self):
        return f"{self.titulo} - {self.autor}"


class UserBookShelf(models.Model):
    SHELF_CHOICES = [
        ('favorito', _('Favorito')),
        ('lendo', _('Lendo')),
        ('vou_ler', _('Quero Ler')),
        ('lido', _('Lido'))
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookshelves')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='shelves')
    shelf_type = models.CharField(_('Tipo de Prateleira'), max_length=20, choices=SHELF_CHOICES)
    added_at = models.DateTimeField(_('Adicionado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)

    class Meta:
        verbose_name = _('Prateleira de Usuário')
        verbose_name_plural = _('Prateleiras de Usuários')
        unique_together = ['user', 'book']
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username} - {self.book.titulo} ({self.get_shelf_type_display()})"

    @staticmethod
    def get_shelf_books(user, shelf_type):
        """Retorna os livros de uma prateleira específica do usuário"""
        return UserBookShelf.objects.filter(
            user=user,
            shelf_type=shelf_type
        ).select_related('book').order_by('-added_at')
from django.db import models
from django.utils.translation import gettext_lazy as _
from pathlib import Path
from cgbookstore.config import settings


class Banner(models.Model):
    """
    Modelo para gerenciar banners do carrossel principal na página inicial.
    Permite controle de período de exibição e ordenação.
    """
    titulo = models.CharField(_('Título'), max_length=200)
    subtitulo = models.CharField(_('Subtítulo'), max_length=300, blank=True)
    descricao = models.TextField(_('Descrição'), blank=True)
    imagem = models.ImageField(_('Imagem'), upload_to='banners/')
    imagem_mobile = models.ImageField(_('Imagem Mobile'), upload_to='banners/mobile/', blank=True, null=True)
    link = models.URLField(_('Link'), max_length=500, blank=True)
    ordem = models.IntegerField(_('Ordem de exibição'), default=0)
    ativo = models.BooleanField(_('Ativo'), default=True)
    data_inicio = models.DateTimeField(_('Data de início'))
    data_fim = models.DateTimeField(_('Data de fim'))
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)

    def get_imagem_url(self):
        """Retorna a URL da imagem ou imagem padrão se não existir"""
        if self.imagem and Path(settings.MEDIA_ROOT).joinpath(self.imagem.name).exists():
            return self.imagem.url
        return f"{settings.STATIC_URL}images/no-banner.svg"

    def get_mobile_url(self):
        """Retorna a URL da imagem mobile ou imagem principal como fallback"""
        if self.imagem_mobile and Path(settings.MEDIA_ROOT).joinpath(self.imagem_mobile.name).exists():
            return self.imagem_mobile.url
        return self.get_imagem_url()

    class Meta:
        ordering = ['ordem', '-data_inicio']
        verbose_name = _('Banner')
        verbose_name_plural = _('Banners')

    def __str__(self):
        return self.titulo
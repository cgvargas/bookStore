from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator


class HomeSection(models.Model):
    """Modelo para gerenciar seções da página inicial"""
    SECTION_TYPES = [
        ('shelf', 'Prateleira de Livros'),
        ('video', 'Seção de Vídeos'),
        ('ad', 'Área de Propaganda'),
        ('link_grid', 'Grade de Links'),
        ('banner', 'Banner Personalizado'),
        ('custom', 'Seção Personalizada'),
    ]

    titulo = models.CharField('Título', max_length=200)
    tipo = models.CharField('Tipo de Seção', max_length=20, choices=SECTION_TYPES)
    ordem = models.IntegerField('Ordem de Exibição', default=0)
    ativo = models.BooleanField('Ativo', default=True)
    css_class = models.CharField('Classe CSS', max_length=100, blank=True)
    descricao = models.TextField('Descrição', blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        ordering = ['ordem', 'titulo']
        verbose_name = 'Seção da Home'
        verbose_name_plural = 'Seções da Home'


class BookShelfSection(models.Model):
    """Modelo para configurar prateleiras de livros"""
    section = models.OneToOneField(
        HomeSection,
        on_delete=models.CASCADE,
        related_name='book_shelf',
        limit_choices_to={'tipo': 'shelf'},
        verbose_name='Seção'
    )
    SHELF_TYPES = [
        ('latest', 'Últimos Adicionados'),
        ('bestsellers', 'Mais Vendidos'),
        ('most_viewed', 'Mais Acessados'),
        ('featured', 'Destaques'),
        ('movies', 'Adaptados para Filme/Série'),
        ('manga', 'Mangás'),
        ('custom', 'Personalizada'),
    ]
    tipo_shelf = models.CharField('Tipo de Prateleira', max_length=20, choices=SHELF_TYPES)
    livros = models.ManyToManyField(
        'Book',
        through='BookShelfItem',
        related_name='home_shelves',
        verbose_name='Livros'
    )
    max_livros = models.IntegerField(
        'Máximo de Livros',
        default=12,
        validators=[MinValueValidator(1), MaxValueValidator(50)]
    )

    class Meta:
        verbose_name = 'Prateleira de Livros'
        verbose_name_plural = 'Prateleiras de Livros'


class BookShelfItem(models.Model):
    """Modelo para ordenar livros nas prateleiras"""
    shelf = models.ForeignKey(
        BookShelfSection,
        on_delete=models.CASCADE,
        verbose_name='Prateleira'
    )
    livro = models.ForeignKey(
        'Book',
        on_delete=models.CASCADE,
        verbose_name='Livro'
    )
    ordem = models.IntegerField('Ordem', default=0)
    added_at = models.DateTimeField('Adicionado em', auto_now_add=True)

    class Meta:
        ordering = ['ordem', '-added_at']
        unique_together = ['shelf', 'livro']
        verbose_name = 'Item da Prateleira'
        verbose_name_plural = 'Itens da Prateleira'


class VideoItem(models.Model):
    """Modelo para vídeos individuais"""
    titulo = models.CharField('Título', max_length=200, blank=True, null=True)
    url = models.URLField('URL do Vídeo')
    thumbnail = models.ImageField('Thumbnail', upload_to='videos/thumbnails/', blank=True)
    ordem = models.IntegerField('Ordem', default=0)
    ativo = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Vídeo'
        verbose_name_plural = 'Vídeos'
        ordering = ['ordem']

    def __str__(self):
        return f"{self.titulo or 'Sem título'}"

class VideoSection(models.Model):
    """Modelo para seções de vídeo"""
    section = models.OneToOneField(
        HomeSection,
        on_delete=models.CASCADE,
        related_name='video_section',
        limit_choices_to={'tipo': 'video'},
        verbose_name='Seção'
    )
    videos = models.ManyToManyField(
        VideoItem,
        related_name='sections',
        verbose_name='Vídeos',
        through='VideoSectionItem'
    )
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Seção de Vídeo'
        verbose_name_plural = 'Seções de Vídeo'

    def __str__(self):
        return f"Seção de Vídeos: {self.section.titulo}"


class VideoSectionItem(models.Model):
    """Modelo para ordenar vídeos nas seções"""
    video_section = models.ForeignKey(VideoSection, on_delete=models.CASCADE)
    video = models.ForeignKey(VideoItem, on_delete=models.CASCADE)
    ordem = models.IntegerField('Ordem', default=0)
    added_at = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        ordering = ['ordem', '-added_at']
        unique_together = ['video_section', 'video']
        verbose_name = 'Item de Vídeo'
        verbose_name_plural = 'Itens de Vídeo'


class Advertisement(models.Model):
    """Modelo para propagandas"""
    section = models.OneToOneField(
        HomeSection,
        on_delete=models.CASCADE,
        related_name='advertisement',
        limit_choices_to={'tipo': 'ad'},
        verbose_name='Seção'
    )
    imagem = models.ImageField('Imagem', upload_to='ads/')
    url = models.URLField('URL de Destino')
    data_inicio = models.DateTimeField('Data de Início')
    data_fim = models.DateTimeField('Data de Término')
    clicks = models.IntegerField('Contagem de Cliques', default=0)

    class Meta:
        verbose_name = 'Propaganda'
        verbose_name_plural = 'Propagandas'


class LinkGridItem(models.Model):
    """Modelo para links com imagens"""
    section = models.ForeignKey(
        HomeSection,
        on_delete=models.CASCADE,
        related_name='link_items',
        limit_choices_to={'tipo': 'link_grid'},
        verbose_name='Seção'
    )
    titulo = models.CharField('Título', max_length=200)
    imagem = models.ImageField('Imagem', upload_to='links/')
    url = models.URLField('URL')
    ordem = models.IntegerField('Ordem', default=0)
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        ordering = ['ordem']
        verbose_name = 'Item da Grade de Links'
        verbose_name_plural = 'Itens da Grade de Links'


class DefaultShelfType(models.Model):
    """Modelo para definir os tipos de prateleiras padrão"""
    nome = models.CharField('Nome', max_length=100)
    identificador = models.CharField('Identificador', max_length=50, unique=True)
    filtro_campo = models.CharField('Campo do Filtro', max_length=50)
    filtro_valor = models.CharField('Valor do Filtro', max_length=50)
    ordem = models.IntegerField('Ordem', default=0)
    ativo = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Tipo de Prateleira Padrão'
        verbose_name_plural = 'Tipos de Prateleiras Padrão'
        ordering = ['ordem']

    def __str__(self):
        return self.nome

    def get_livros(self):
        """Retorna os livros filtrados baseado nas configurações"""
        from .book import Book

        if self.filtro_campo == 'e_lancamento':
            return Book.objects.filter(e_lancamento=True).order_by('-created_at')
        elif self.filtro_campo == 'e_destaque':
            return Book.objects.filter(e_destaque=True).order_by('ordem_exibicao')
        elif self.filtro_campo == 'quantidade_vendida':
            return Book.objects.filter(quantidade_vendida__gt=0).order_by('-quantidade_vendida')
        elif self.filtro_campo == 'adaptado_filme':
            return Book.objects.filter(adaptado_filme=True).order_by('ordem_exibicao')
        elif self.filtro_campo == 'e_manga':
            return Book.objects.filter(e_manga=True).order_by('ordem_exibicao')
        return Book.objects.none()
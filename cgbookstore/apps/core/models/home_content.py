# Arquivo: cgbookstore/apps/core/models/home_content.py

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.db.models import Q
from django.db.models.query import QuerySet
import logging

logger = logging.getLogger(__name__)

# ==============================================================================
# MODELO PRINCIPAL DE SEÇÃO
# ==============================================================================

class HomeSection(models.Model):
    """
    Modelo unificado para gerenciar TODAS as seções da página inicial,
    incluindo a lógica completa para prateleiras de livros.
    """
    # Tipos de Seção
    SECTION_TYPES = [
        ('shelf', 'Prateleira de Livros'),
        ('video', 'Seção de Vídeos'),
        ('author', 'Seção de Autores'),
        ('ad', 'Área de Propaganda'),
        ('link_grid', 'Grade de Links'),
        ('banner', 'Banner Personalizado'),
        ('custom', 'Seção Genérica'),
        ('background', 'Imagem de Fundo do Site'),
    ]

    # Tipos de Prateleira (como ela obtém os livros)
    SHELF_BEHAVIOR_CHOICES = [
        ('manual', 'Seleção Manual de Livros'),
        ('automatic', 'Filtro Automático'),
    ]

    # Opções de Filtro Automático (à prova de erros)
    SHELF_FILTER_CHOICES = [
        ('e_lancamento', 'É Lançamento'),
        ('e_destaque', 'É Destaque'),
        ('bestsellers', 'Mais Vendidos (por quantidade vendida)'),
        ('most_viewed', 'Mais Acessados (por quantidade de acessos)'),
        ('adaptado_filme', 'Adaptado para Filme/Série'),
        ('e_manga', 'É Mangá'),
        ('categoria__icontains', 'Categoria (contém texto)'),
        ('autor__icontains', 'Autor (contém texto)'),
        ('titulo__icontains', 'Título (contém texto)'),
    ]

    # --- CAMPOS PRINCIPAIS (PARA TODAS AS SEÇÕES) ---
    titulo = models.CharField('Título da Seção', max_length=200)
    tipo = models.CharField('Tipo de Seção', max_length=20, choices=SECTION_TYPES)
    ordem = models.IntegerField('Ordem de Exibição', default=0)
    ativo = models.BooleanField('Ativo', default=True)

    # --- CAMPOS ESPECÍFICOS PARA PRATELEIRAS DE LIVROS (tipo='shelf') ---
    shelf_behavior = models.CharField(
        'Tipo de Prateleira', max_length=20, choices=SHELF_BEHAVIOR_CHOICES,
        blank=True, help_text="Escolha como os livros desta prateleira serão selecionados."
    )
    shelf_filter_field = models.CharField(
        'Filtro Automático', max_length=50, choices=SHELF_FILTER_CHOICES,
        blank=True, help_text="Usado apenas se o tipo for 'Filtro Automático'."
    )
    shelf_filter_value = models.CharField(
        'Valor para o Filtro', max_length=100,
        blank=True, help_text="Ex: 'Ficção Científica' para o filtro de Categoria."
    )
    manual_books = models.ManyToManyField(
        'Book', through='HomeSectionBookItem', related_name='home_sections',
        blank=True, verbose_name='Livros Manuais'
    )
    max_books = models.IntegerField('Máximo de Livros', default=12, validators=[MinValueValidator(1), MaxValueValidator(50)])

    # --- CAMPOS PARA PERSONALIZAÇÃO FUTURA ---
    customization_options = models.JSONField(
        'Opções de Personalização (JSON)', blank=True, null=True,
        help_text="Configurações avançadas como cores, transparência, formato de cards, etc."
    )
    css_class = models.CharField('Classe CSS Adicional', max_length=100, blank=True)

    # --- CAMPOS DE AUDITORIA ---
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)


    class Meta:
        ordering = ['ordem', 'titulo']
        verbose_name = 'Seção da Home'
        verbose_name_plural = 'Seções da Home'

    def __str__(self):
        return f"{self.ordem}: {self.titulo} ({self.get_tipo_display()})"

    def get_books(self) -> QuerySet:
        """
        Lógica centralizada para buscar os livros de uma prateleira.
        """
        from .book import Book

        if self.tipo != 'shelf':
            return Book.objects.none()

        if self.shelf_behavior == 'manual':
            return self.manual_books.all().order_by('homesectionbookitem__ordem')

        elif self.shelf_behavior == 'automatic':
            campo = self.shelf_filter_field
            valor = self.shelf_filter_value

            boolean_fields = ['e_lancamento', 'e_destaque', 'adaptado_filme', 'e_manga']
            if campo in boolean_fields:
                return Book.objects.filter(ativo=True, **{campo: True})[:self.max_books]

            if campo == 'bestsellers':
                return Book.objects.filter(ativo=True, quantidade_vendida__gt=0).order_by('-quantidade_vendida')[:self.max_books]
            if campo == 'most_viewed':
                return Book.objects.filter(ativo=True, quantidade_acessos__gt=0).order_by('-quantidade_acessos')[:self.max_books]

            if valor:
                return Book.objects.filter(ativo=True, **{campo: valor})[:self.max_books]

        return Book.objects.none()


class HomeSectionBookItem(models.Model):
    """
    Modelo 'through' para definir a ordem dos livros em uma prateleira manual.
    """
    section = models.ForeignKey(HomeSection, on_delete=models.CASCADE)
    book = models.ForeignKey('Book', on_delete=models.CASCADE)
    ordem = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordem']
        unique_together = ['section', 'book']


# ------------------------------------------------------------------------------
# Modelos para gerenciamento de seções de vídeo
# ------------------------------------------------------------------------------

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
    # Relação com a seção da página inicial
    section = models.OneToOneField(
        HomeSection,
        on_delete=models.CASCADE,
        related_name='video_section',
        limit_choices_to={'tipo': 'video'},  # Restringe a seções do tipo vídeo
        verbose_name='Seção'
    )
    # Relacionamento M2M com vídeos através de modelo intermediário para ordenação
    videos = models.ManyToManyField(
        VideoItem,
        related_name='sections',
        verbose_name='Vídeos',
        through='VideoSectionItem'
    )
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Seção Vídeo'
        verbose_name_plural = 'Seções Vídeo'

    def __str__(self):
        return f"Seção de Vídeos: {self.section.titulo}"


class VideoSectionItem(models.Model):
    """Modelo para ordenar vídeos nas seções"""
    # Modelo intermediário para relacionamento M2M ordenado entre seção e vídeos
    video_section = models.ForeignKey(VideoSection, on_delete=models.CASCADE)
    video = models.ForeignKey(VideoItem, on_delete=models.CASCADE)
    ordem = models.IntegerField('Ordem', default=0)
    added_at = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        ordering = ['ordem', '-added_at']
        unique_together = ['video_section', 'video']  # Impede duplicidade de vídeos na mesma seção
        verbose_name = 'Item de Vídeo'
        verbose_name_plural = 'Itens de Vídeo'


# ------------------------------------------------------------------------------
# Modelos para gerenciamento de propagandas e links
# ------------------------------------------------------------------------------

class Advertisement(models.Model):
    """Modelo para propagandas"""
    section = models.OneToOneField(
        HomeSection,
        on_delete=models.CASCADE,
        related_name='advertisement',
        limit_choices_to={'tipo': 'ad'},  # Restringe a seções do tipo propaganda
        verbose_name='Seção'
    )
    imagem = models.ImageField('Imagem', upload_to='ads/')
    url = models.URLField('URL de Destino')
    data_inicio = models.DateTimeField('Data de Início')
    data_fim = models.DateTimeField('Data de Término')
    clicks = models.IntegerField('Contagem de Cliques', default=0)

    class Meta:
        verbose_name = 'Anúncio'
        verbose_name_plural = 'Anúncios'


class LinkGridItem(models.Model):
    """Modelo para links com imagens"""
    # Relacionamento direto com a seção da home (sem modelo intermediário)
    section = models.ForeignKey(
        HomeSection,
        on_delete=models.CASCADE,
        related_name='link_items',
        limit_choices_to={'tipo': 'link_grid'},  # Restringe a seções do tipo grade de links
        verbose_name='Seção'
    )
    titulo = models.CharField('Título', max_length=200)
    imagem = models.ImageField('Imagem', upload_to='links/')
    url = models.URLField('URL')
    ordem = models.IntegerField('Ordem', default=0)
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        ordering = ['ordem']
        verbose_name = 'Link'
        verbose_name_plural = 'Links'


# ------------------------------------------------------------------------------
# Sistema de seções personalizadas com tipos e layouts flexíveis
# ------------------------------------------------------------------------------

class CustomSectionType(models.Model):
    """Modelo para definir tipos de seções personalizadas"""
    nome = models.CharField('Nome', max_length=100)
    identificador = models.CharField('Identificador', max_length=50, unique=True)
    ativo = models.BooleanField('Ativo', default=True)
    descricao = models.TextField('Descrição', blank=True)
    metadados = models.JSONField('Metadados', blank=True, null=True)  # Armazena configurações específicas do tipo
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Tipo Seção'
        verbose_name_plural = 'Tipos Seção'
        ordering = ['nome']

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        # Gera identificador automático a partir do nome se não fornecido
        if not self.identificador:
            self.identificador = slugify(self.nome)
        super().save(*args, **kwargs)


class CustomSectionLayout(models.Model):
    """Modelo para definir layouts disponíveis para seções personalizadas"""
    nome = models.CharField('Nome', max_length=100)
    identificador = models.CharField('Identificador', max_length=50, unique=True)
    section_type = models.ForeignKey(
        CustomSectionType,
        on_delete=models.CASCADE,
        related_name='layouts',
        verbose_name='Tipo de Seção'
    )
    template_path = models.CharField('Caminho do Template', max_length=200)
    imagem_preview = models.ImageField('Imagem de Preview', upload_to='layouts/', blank=True)
    ativo = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Layout'
        verbose_name_plural = 'Layouts'
        ordering = ['section_type', 'nome']

    def __str__(self):
        return f"{self.nome} ({self.section_type.nome})"

    def save(self, *args, **kwargs):
        # Gera identificador automático a partir do nome se não fornecido
        if not self.identificador:
            self.identificador = slugify(self.nome)
        super().save(*args, **kwargs)


class CustomSection(models.Model):
    """Modelo para configurar seções personalizadas na home"""
    section = models.OneToOneField(
        'HomeSection',
        on_delete=models.CASCADE,
        related_name='custom_section',
        limit_choices_to={'tipo': 'custom'},  # Restringe a seções do tipo personalizado
        verbose_name='Seção'
    )
    section_type = models.ForeignKey(
        CustomSectionType,
        on_delete=models.CASCADE,
        related_name='custom_sections',
        verbose_name='Tipo de Conteúdo'
    )
    layout = models.ForeignKey(
        CustomSectionLayout,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sections',
        verbose_name='Layout'
    )
    ativo = models.BooleanField('Ativo', default=True)

    config_json = models.JSONField(
        'Configurações Adicionais (JSON)',
        blank=True,
        null=True,
        help_text='Configurações específicas em formato JSON para este layout.'
    )

    class Meta:
        verbose_name = 'Seção Especial'
        verbose_name_plural = 'Seções Especiais'

    def __str__(self):
        return f"Seção: {self.section.titulo} ({self.section_type.nome})"

    def clean(self):
        """Valida que o layout pertence ao tipo de seção selecionado"""
        # Validação de integridade para garantir compatibilidade entre layout e tipo de seção
        if self.layout and self.layout.section_type != self.section_type:
            raise ValidationError({
                'layout': 'O layout selecionado não é compatível com o tipo de seção escolhido.'
            })


class EventItem(models.Model):
    """Modelo para eventos literários individuais"""
    # Exemplo de implementação específica para um tipo de seção personalizada (eventos)
    titulo = models.CharField('Título', max_length=200)
    data_evento = models.DateTimeField('Data do Evento')
    local = models.CharField('Local', max_length=200, blank=True)
    descricao = models.TextField('Descrição', blank=True)
    imagem = models.ImageField('Imagem', upload_to='events/', blank=True)
    url = models.URLField('Link para inscrição/detalhes', blank=True)
    em_destaque = models.BooleanField('Em Destaque', default=False)
    ordem = models.IntegerField('Ordem', default=0)
    ativo = models.BooleanField('Ativo', default=True)
    custom_section = models.ForeignKey(
        CustomSection,
        on_delete=models.SET_NULL,
        related_name='events',
        verbose_name='Seção Personalizada',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'
        ordering = ['ordem', 'data_evento']

    def __str__(self):
        return f"{self.titulo} ({self.data_evento.strftime('%d/%m/%Y')})"


class BackgroundSettings(models.Model):
    """Modelo para gerenciar a imagem de fundo do site"""
    section = models.OneToOneField(
        HomeSection,
        on_delete=models.CASCADE,
        related_name='background_settings',
        limit_choices_to={'tipo': 'background'},  # Restringe a seções do tipo background
        verbose_name='Seção'
    )
    imagem = models.ImageField('Imagem de Fundo', upload_to='backgrounds/')
    opacidade = models.IntegerField(
        'Opacidade do Esmaecimento (%)',
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Define a intensidade do esmaecimento nas bordas (0-100%)'
    )
    habilitado = models.BooleanField('Habilitado', default=True)
    aplicar_em = models.CharField(
        'Aplicar em',
        max_length=20,
        choices=[
            ('both', 'Ambos os temas'),
            ('light', 'Apenas tema claro'),
            ('dark', 'Apenas tema escuro')
        ],
        default='both'
    )
    posicao = models.CharField(
        'Posição',
        max_length=20,
        choices=[
            ('center', 'Centralizado'),
            ('top', 'Superior'),
            ('bottom', 'Inferior')
        ],
        default='center'
    )
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Configuração de Background'
        verbose_name_plural = 'Configurações de Background'

    def __str__(self):
        return f"Background: {self.section.titulo}"
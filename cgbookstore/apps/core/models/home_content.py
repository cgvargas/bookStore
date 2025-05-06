from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils.text import slugify

# ------------------------------------------------------------------------------
# Sistema de gerenciamento de conteúdo da página inicial
# Este módulo implementa uma arquitetura modular e flexível para gerenciar
# diferentes tipos de seções na página inicial do site.
# ------------------------------------------------------------------------------

class HomeSection(models.Model):
    """Modelo para gerenciar seções da página inicial"""
    # Define os tipos de seções disponíveis para a página inicial
    SECTION_TYPES = [
        ('shelf', 'Prateleira de Livros'),
        ('video', 'Seção de Vídeos'),
        ('ad', 'Área de Propaganda'),
        ('link_grid', 'Grade de Links'),
        ('banner', 'Banner Personalizado'),
        ('custom', 'Seção Personalizada'),
        ('background', 'Imagem de Fundo do Site'),
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
        verbose_name = 'Seção'
        verbose_name_plural = 'Seções'

    def __str__(self):
        return self.titulo

    def get_template_name(self):
        """
        Retorna o caminho para o template a ser usado para renderizar esta seção.
        """
        templates = {
            'shelf': 'core/includes/book_shelf.html',
            'video': 'core/includes/video_section.html',
            'ad': 'core/includes/advertisement.html',
            'link_grid': 'core/includes/link_grid.html',
            'custom': None  # Para seções personalizadas, o template é definido dinamicamente
        }

        # Para seções personalizadas, busca o template do layout selecionado
        if self.tipo == 'custom' and hasattr(self, 'custom_section'):
            try:
                custom_section = self.custom_section
                if custom_section and custom_section.layout and hasattr(custom_section.layout, 'template_path'):
                    return custom_section.layout.template_path
            except Exception:
                pass

        return templates.get(self.tipo)


# ------------------------------------------------------------------------------
# Modelos para gerenciamento de prateleiras de livros
# O sistema permite configurar diferentes tipos de prateleiras automatizadas ou
# personalizadas com livros específicos.
# ------------------------------------------------------------------------------

class DefaultShelfType(models.Model):
    """Modelo para definir os tipos de prateleiras padrão"""
    nome = models.CharField('Nome', max_length=100)
    identificador = models.CharField('Identificador', max_length=50, unique=True)
    # Os campos filtro_campo e filtro_valor são usados para criar filtros dinâmicos
    filtro_campo = models.CharField('Campo do Filtro', max_length=50)
    filtro_valor = models.CharField('Valor do Filtro', max_length=50)
    ordem = models.IntegerField('Ordem', default=0)
    ativo = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Prateleira Padrão'
        verbose_name_plural = 'Prateleiras Padrão'
        ordering = ['ordem']

    def __str__(self):
        return self.nome

    def get_livros(self):
        """Retorna os livros filtrados baseado nas configurações"""
        from .book import Book
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"Buscando livros para prateleira: {self.nome} ({self.identificador})")

        try:
            # Implementa lógica para diferentes tipos de filtros de livros
            # Casos especiais tratados individualmente
            if self.identificador == 'ebooks':
                return Book.objects.filter(tipo_shelf_especial=self.identificador).order_by('ordem_exibicao')

            # Para tipos padrão, usa os campos booleanos correspondentes
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
            elif self.filtro_campo == 'tipo_shelf_especial':
                return Book.objects.filter(tipo_shelf_especial=self.filtro_valor).order_by('ordem_exibicao')

            # Filtragem dinâmica - usado quando nenhum dos casos específicos se aplica
            return Book.objects.filter(**{self.filtro_campo: self.filtro_valor}).order_by('ordem_exibicao')

        except Exception as e:
            logger.error(f"Erro ao filtrar: {str(e)}")
            # Retorna queryset vazio em caso de erro
            return Book.objects.none()


class BookShelfSection(models.Model):
    """Modelo para configurar prateleiras de livros"""
    # Relação com a seção da página inicial
    section = models.OneToOneField(
        HomeSection,
        on_delete=models.CASCADE,
        related_name='book_shelf',
        limit_choices_to={'tipo': 'shelf'},  # Restringe a seções do tipo prateleira
        verbose_name='Seção'
    )

    # Sistema de compatibilidade para código legado
    SHELF_TYPES = [
        ('latest', 'Últimos Adicionados'),
        ('bestsellers', 'Mais Vendidos'),
        ('most_viewed', 'Mais Acessados'),
        ('featured', 'Destaques'),
        ('movies', 'Adaptados para Filme/Série'),
        ('manga', 'Mangás'),
        ('custom', 'Personalizada'),
    ]

    # Sistema atual usando ForeignKey para tipos de prateleira configuráveis
    shelf_type = models.ForeignKey(
        DefaultShelfType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Tipo de Prateleira Personalizada'
    )

    # Campo mantido para compatibilidade com código existente
    tipo_shelf = models.CharField(
        'Tipo de Prateleira (Legado)',
        max_length=20,
        choices=SHELF_TYPES,
        blank=True,
        help_text='Usado apenas para compatibilidade. Preferir o campo "Tipo de Prateleira Personalizada".'
    )

    # Relacionamento muitos-para-muitos com livros através de uma tabela intermediária
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
        verbose_name = 'Prateleira'
        verbose_name_plural = 'Prateleiras'

    def __str__(self):
        return f"Prateleira: {self.section.titulo}"

    def get_tipo_identificador(self):
        """Retorna o identificador do tipo de prateleira"""
        if self.shelf_type:
            return self.shelf_type.identificador
        return self.tipo_shelf

    def get_tipo_shelf_display(self):
        """Retorna o nome formatado do tipo de prateleira legado"""
        if not self.tipo_shelf:
            return ''
        return dict(self.SHELF_TYPES).get(self.tipo_shelf, self.tipo_shelf)

    def get_filtered_books(self):
        """Obtém livros filtrados baseados no tipo de prateleira"""
        from .book import Book

        # Implementa sistema com fallback entre novo modelo e legado
        # Primeiro, tenta usar o shelf_type se estiver definido
        if self.shelf_type:
            return self.shelf_type.get_livros()

        # Se não, usa a lógica legada baseada no tipo_shelf
        if self.tipo_shelf == 'latest':
            return Book.objects.all().order_by('-created_at')
        elif self.tipo_shelf == 'bestsellers':
            return Book.objects.filter(quantidade_vendida__gt=0).order_by('-quantidade_vendida')
        elif self.tipo_shelf == 'most_viewed':
            return Book.objects.filter(quantidade_acessos__gt=0).order_by('-quantidade_acessos')
        elif self.tipo_shelf == 'featured':
            return Book.objects.filter(e_destaque=True).order_by('ordem_exibicao')
        elif self.tipo_shelf == 'movies':
            return Book.objects.filter(adaptado_filme=True).order_by('ordem_exibicao')
        elif self.tipo_shelf == 'manga':
            return Book.objects.filter(e_manga=True).order_by('ordem_exibicao')

        # Se for custom ou nenhum dos anteriores, retorna lista vazia
        return Book.objects.none()


class BookShelfItem(models.Model):
    """Modelo para ordenar livros nas prateleiras"""
    # Modelo intermediário para relacionamento M2M ordenado entre prateleira e livros
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
        unique_together = ['shelf', 'livro']  # Impede duplicidade de livros na mesma prateleira
        verbose_name = 'Item da Prateleira'
        verbose_name_plural = 'Itens da Prateleira'


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
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name='Seção Personalizada'
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
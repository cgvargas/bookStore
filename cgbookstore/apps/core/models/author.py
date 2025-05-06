from django.db import models
from django.utils.text import slugify


class Author(models.Model):
    """Modelo para gerenciar autores de livros"""
    nome = models.CharField('Nome', max_length=200)
    sobrenome = models.CharField('Sobrenome', max_length=200, blank=True)
    slug = models.SlugField('Slug', max_length=250, unique=True, blank=True)
    foto = models.ImageField('Foto', upload_to='autores/', blank=True, null=True)
    biografia = models.TextField('Biografia', blank=True)
    data_nascimento = models.DateField('Data de Nascimento', blank=True, null=True)
    nacionalidade = models.CharField('Nacionalidade', max_length=100, blank=True)
    website = models.URLField('Website', blank=True)
    twitter = models.CharField('Twitter', max_length=100, blank=True)
    instagram = models.CharField('Instagram', max_length=100, blank=True)
    facebook = models.CharField('Facebook', max_length=100, blank=True)
    destaque = models.BooleanField('Destaque', default=False)
    ordem = models.IntegerField('Ordem', default=0)
    ativo = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Autor'
        verbose_name_plural = 'Autores'
        ordering = ['nome', 'sobrenome']

    def __str__(self):
        if self.sobrenome:
            return f"{self.nome} {self.sobrenome}"
        return self.nome

    def save(self, *args, **kwargs):
        """Gera automaticamente o slug se não for fornecido"""
        if not self.slug:
            nome_completo = f"{self.nome} {self.sobrenome}".strip()
            self.slug = slugify(nome_completo)
        super().save(*args, **kwargs)

    def get_nome_completo(self):
        """Retorna o nome completo do autor"""
        if self.sobrenome:
            return f"{self.nome} {self.sobrenome}"
        return self.nome

    def get_livros(self):
        """Retorna todos os livros deste autor"""
        return self.books.all()

    def get_livros_count(self):
        """Retorna o número de livros deste autor"""
        return self.books.count()


class AuthorSection(models.Model):
    """Modelo para configurar seções de autores na página inicial"""
    section = models.OneToOneField(
        'HomeSection',
        on_delete=models.CASCADE,
        related_name='author_section',
        limit_choices_to={'tipo': 'custom'},  # Usa o tipo custom para aproveitar estrutura existente
        verbose_name='Seção'
    )
    titulo_secundario = models.CharField('Subtítulo', max_length=200, blank=True)
    descricao = models.TextField('Descrição da Seção', blank=True)
    mostrar_biografia = models.BooleanField('Mostrar Biografia', default=True)
    apenas_destaque = models.BooleanField('Apenas Autores em Destaque', default=False)
    max_autores = models.IntegerField('Máximo de Autores', default=4)
    ordem_exibicao = models.CharField(
        'Ordenar por',
        max_length=20,
        choices=[
            ('nome', 'Nome'),
            ('livros', 'Quantidade de Livros'),
            ('recentes', 'Mais Recentes'),
            ('manual', 'Ordem Manual')
        ],
        default='nome'
    )
    autores = models.ManyToManyField(
        Author,
        through='AuthorSectionItem',
        related_name='sections',
        verbose_name='Autores'
    )
    ativo = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Seção de Autores'
        verbose_name_plural = 'Seções de Autores'

    def __str__(self):
        return f"Autores: {self.section.titulo}"

    def get_autores(self):
        """Retorna os autores conforme configuração da seção"""
        if self.ordem_exibicao == 'manual':
            # Retorna autores na ordem manual definida
            return Author.objects.filter(
                authorsectionitem__author_section=self
            ).order_by('authorsectionitem__ordem')

        # Filtragem base
        queryset = Author.objects.filter(ativo=True)

        # Aplicar filtro de destaque se necessário
        if self.apenas_destaque:
            queryset = queryset.filter(destaque=True)

        # Aplicar ordenação
        if self.ordem_exibicao == 'livros':
            # Ordenação por quantidade de livros requer annotation
            from django.db.models import Count
            queryset = queryset.annotate(
                livros_count=Count('books')
            ).order_by('-livros_count')
        elif self.ordem_exibicao == 'recentes':
            queryset = queryset.order_by('-created_at')
        else:  # Padrão: nome
            queryset = queryset.order_by('nome', 'sobrenome')

        return queryset[:self.max_autores]


class AuthorSectionItem(models.Model):
    """Modelo para ordenar autores nas seções"""
    author_section = models.ForeignKey(
        AuthorSection,
        on_delete=models.CASCADE,
        verbose_name='Seção de Autores'
    )
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        verbose_name='Autor'
    )
    ordem = models.IntegerField('Ordem', default=0)
    added_at = models.DateTimeField('Adicionado em', auto_now_add=True)

    class Meta:
        ordering = ['ordem', '-added_at']
        unique_together = ['author_section', 'author']  # Impede duplicidade
        verbose_name = 'Item de Autor'
        verbose_name_plural = 'Itens de Autor'

    def __str__(self):
        return f"{self.author} - {self.author_section}"
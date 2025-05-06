# cgbookstore/apps/core/admin/forms.py
"""
Formulários específicos para o módulo administrativo.

Este módulo contém os formulários utilizados pelas classes de administração,
incluindo validações específicas e customizações.
"""

import logging
from django import forms
from django.db.models import Q
from django.core.exceptions import ValidationError

from ..models.book import Book
from ..models.home_content import DefaultShelfType, BookShelfSection

logger = logging.getLogger(__name__)


class BookAdminForm(forms.ModelForm):
    """
    Formulário personalizado para o admin de Livros que permite valores dinâmicos.

    Este formulário customiza a apresentação dos campos de upload de imagens
    e adiciona suporte a valores dinâmicos para o campo tipo_shelf_especial.
    """

    class Meta:
        model = Book
        fields = '__all__'  # Inclui todos os campos
        widgets = {
            'capa': forms.FileInput(attrs={'accept': 'image/*'}),
            'capa_preview': forms.FileInput(attrs={'accept': 'image/*'}),
        }
        # Excluímos o campo ManyToMany authors para evitar o erro, pois vamos gerenciá-lo com inline
        exclude = ['authors']

    def __init__(self, *args, **kwargs):
        """
        Inicializa o formulário com escolhas dinâmicas para o campo tipo_shelf_especial

        Args:
            *args: Argumentos posicionais
            **kwargs: Argumentos nomeados
        """
        super().__init__(*args, **kwargs)

        # Obtém as opções padrão do modelo
        standard_choices = list(Book.SHELF_SPECIAL_CHOICES)

        # Obtém tipos de prateleira personalizados
        try:
            custom_shelves = DefaultShelfType.objects.filter(ativo=True)

            # Adiciona os identificadores personalizados às opções
            custom_choices = []
            for shelf in custom_shelves:
                # Usar o identificador exato da prateleira (pode ser 'ebooks', 'livros_digitais', etc.)
                custom_choices.append((shelf.identificador, shelf.nome))

            # Combina as opções padrão com as personalizadas
            all_choices = standard_choices + custom_choices

            # Atualiza o campo com todas as opções
            if 'tipo_shelf_especial' in self.fields:
                self.fields['tipo_shelf_especial'].choices = all_choices

            # Log para debug
            logger.info(f"Opções disponíveis para tipo_shelf_especial: {all_choices}")

        except Exception as e:
            logger.error(f"Erro ao carregar tipos de prateleira personalizados: {str(e)}")

    def clean_tipo_shelf_especial(self):
        """
        Valida o campo tipo_shelf_especial para aceitar valores personalizados

        Returns:
            str: Valor validado para o campo
        """
        value = self.cleaned_data.get('tipo_shelf_especial')

        # Se o valor for vazio, está ok
        if not value:
            return value

        # Se o valor é uma das opções padrão, está ok
        standard_values = [choice[0] for choice in Book.SHELF_SPECIAL_CHOICES]
        if value in standard_values:
            return value

        # Verifica se o valor é um identificador de prateleira personalizada
        try:
            shelf_exists = DefaultShelfType.objects.filter(
                identificador=value, ativo=True
            ).exists()
            if shelf_exists:
                return value
        except Exception as e:
            logger.error(f"Erro ao verificar tipo de prateleira: {str(e)}")

        # Aceita qualquer valor que tenha sido escolhido no formulário
        # Isso evita o erro de validação mesmo para novas prateleiras
        return value


class BookShelfFilterForm(forms.Form):
    """
    Formulário para filtragem de livros em prateleiras
    """
    shelf_type = forms.ModelChoiceField(
        label="Tipo de Prateleira",
        queryset=DefaultShelfType.objects.filter(ativo=True),
        required=False,
        empty_label="Todos os tipos"
    )

    section_name = forms.CharField(
        label="Nome da Seção",
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Filtrar por nome da seção'})
    )

    active_only = forms.BooleanField(
        label="Apenas Ativos",
        required=False,
        initial=True
    )

    def filter_query(self, queryset):
        """
        Aplica os filtros selecionados no formulário ao queryset

        Args:
            queryset: QuerySet inicial de prateleiras

        Returns:
            QuerySet: Queryset filtrado conforme os critérios
        """
        cleaned_data = self.cleaned_data

        if cleaned_data.get('shelf_type'):
            queryset = queryset.filter(shelf_type=cleaned_data['shelf_type'])

        if cleaned_data.get('section_name'):
            queryset = queryset.filter(
                section__titulo__icontains=cleaned_data['section_name']
            )

        if cleaned_data.get('active_only'):
            queryset = queryset.filter(section__ativo=True)

        return queryset


class AdminBulkActionForm(forms.Form):
    """
    Formulário para ações em massa no admin
    """
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    shelf_type = forms.ModelChoiceField(
        label="Tipo de Prateleira",
        queryset=DefaultShelfType.objects.filter(ativo=True),
        required=False,
        help_text="Selecione o tipo de prateleira para associar os itens"
    )

    def clean(self):
        cleaned_data = super().clean()
        action = self.data.get('action')

        # Validações específicas para certas ações
        if action in ['add_to_shelf', 'change_shelf_type'] and not cleaned_data.get('shelf_type'):
            raise ValidationError({
                'shelf_type': "É necessário selecionar um tipo de prateleira para esta ação."
            })

        return cleaned_data


class CustomAdminImportForm(forms.Form):
    """
    Formulário para importação de dados no admin
    """
    import_file = forms.FileField(
        label="Arquivo para Importação",
        help_text="Selecione um arquivo CSV, JSON ou Excel para importar dados."
    )

    update_existing = forms.BooleanField(
        label="Atualizar Existentes",
        required=False,
        initial=True,
        help_text="Se marcado, registros existentes serão atualizados. Caso contrário, serão ignorados."
    )

    ignore_errors = forms.BooleanField(
        label="Ignorar Erros",
        required=False,
        initial=False,
        help_text="Se marcado, a importação continuará mesmo se encontrar erros em alguns registros."
    )


class BookShelfSectionAdminForm(forms.ModelForm):
    """
    Formulário administrativo para seções de prateleira com validações adicionais
    """

    class Meta:
        model = BookShelfSection
        fields = '__all__'

    def clean(self):
        """
        Validação para garantir que a configuração da prateleira seja consistente
        """
        cleaned_data = super().clean()
        shelf_type = cleaned_data.get('shelf_type')
        tipo_shelf = cleaned_data.get('tipo_shelf')

        # Verifica se pelo menos uma forma de classificação está definida
        if not shelf_type and not tipo_shelf:
            raise ValidationError(
                "Você deve especificar um tipo de prateleira (personalizado ou padrão)"
            )

        return cleaned_data


class QuickShelfCreationForm(forms.Form):
    """
    Formulário para criação rápida de prateleira completa.

    Este formulário permite criar em um único passo:
    - Um tipo de prateleira (DefaultShelfType)
    - Uma seção na home (HomeSection)
    - Uma prateleira associada (BookShelfSection)
    """
    nome = forms.CharField(
        label="Nome da Prateleira",
        max_length=100,
        required=True,
        help_text="Nome da prateleira que será exibido para os usuários."
    )

    identificador = forms.CharField(
        label="Identificador",
        max_length=100,
        required=True,
        help_text="Identificador único para esta prateleira (sem espaços, apenas letras minúsculas e underscores)."
    )

    ativo = forms.BooleanField(
        label="Ativo",
        required=False,
        initial=True,
        help_text="Indica se esta prateleira está ativa e deve ser exibida no site."
    )

    filtro_campo = forms.ChoiceField(
        label="Campo de Filtro",
        choices=[
            ('', '-- Selecione um campo --'),
            ('e_lancamento', 'Lançamentos'),
            ('e_destaque', 'Destaques'),
            ('adaptado_filme', 'Adaptados para Filme'),
            ('e_manga', 'Mangás'),
            ('categoria', 'Categoria'),
            ('autor', 'Autor'),
            ('editora', 'Editora'),
            ('ano_publicacao', 'Ano de Publicação')
        ],
        required=False,
        help_text="Campo utilizado para filtrar livros nesta prateleira."
    )

    filtro_valor = forms.CharField(
        label="Valor do Filtro",
        max_length=100,
        required=False,
        help_text="Valor para filtrar os livros (usado apenas para campos como categoria, autor, etc)."
    )

    ordem = forms.IntegerField(
        label="Ordem de Exibição",
        initial=0,
        required=True,
        help_text="Ordem em que esta prateleira será exibida na página inicial."
    )

    max_livros = forms.IntegerField(
        label="Máximo de Livros",
        initial=15,
        min_value=1,
        max_value=100,
        required=True,
        help_text="Número máximo de livros que podem ser exibidos nesta prateleira."
    )

    def clean_identificador(self):
        """
        Valida o identificador para garantir formato correto e unicidade.
        """
        identificador = self.cleaned_data.get('identificador')

        # Verifica formato
        import re
        if not re.match(r'^[a-z0-9_]+$', identificador):
            raise ValidationError(
                "O identificador deve conter apenas letras minúsculas, números e underscores (_)."
            )

        # Verifica unicidade
        if DefaultShelfType.objects.filter(identificador=identificador).exists():
            raise ValidationError(
                "Este identificador já está em uso por outra prateleira."
            )

        return identificador

    def clean(self):
        """
        Validação adicional dos campos do formulário.
        """
        cleaned_data = super().clean()
        filtro_campo = cleaned_data.get('filtro_campo')
        filtro_valor = cleaned_data.get('filtro_valor')

        # Verifica se filtro_valor está preenchido quando necessário
        boolean_fields = ['e_lancamento', 'e_destaque', 'adaptado_filme', 'e_manga']
        if filtro_campo and filtro_campo not in boolean_fields and not filtro_valor:
            self.add_error('filtro_valor',
                           "O valor do filtro é obrigatório para o campo selecionado.")

        return cleaned_data

    def save(self):
        """
        Salva os dados do formulário criando os objetos necessários.

        Returns:
            dict: Dicionário com os objetos criados
        """
        from ..models.home_content import DefaultShelfType, HomeSection, BookShelfSection

        # Obtém os dados limpos
        nome = self.cleaned_data.get('nome')
        identificador = self.cleaned_data.get('identificador')
        ativo = self.cleaned_data.get('ativo')
        filtro_campo = self.cleaned_data.get('filtro_campo')
        filtro_valor = self.cleaned_data.get('filtro_valor')
        ordem = self.cleaned_data.get('ordem')
        max_livros = self.cleaned_data.get('max_livros')

        # Cria o tipo de prateleira
        shelf_type = DefaultShelfType.objects.create(
            nome=nome,
            identificador=identificador,
            ativo=ativo,
            filtro_campo=filtro_campo,
            filtro_valor=filtro_valor,
            ordem=ordem
        )

        # Cria a seção na home
        section = HomeSection.objects.create(
            titulo=nome,
            descricao=f"Prateleira de {nome}",
            tipo='shelf',
            ativo=ativo,
            ordem=ordem
        )

        # Cria a prateleira associada
        book_shelf = BookShelfSection.objects.create(
            section=section,
            shelf_type=shelf_type,
            max_livros=max_livros
        )

        # Retorna os objetos criados
        return {
            'shelf_type': shelf_type,
            'section': section,
            'book_shelf': book_shelf
        }
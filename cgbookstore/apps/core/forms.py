# apps/core/forms.py
"""
Módulo de formulários para a aplicação CG BookStore.

Contém formulários para:
- Registro de usuário
- Atualização de perfil
- Formulário de contato
- Criação rápida de prateleiras

Inclui validações personalizadas para campos como CPF, email,
data de nascimento e senha.
"""

import re
from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator
from datetime import date
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django.core.mail import send_mail
from django.template import loader
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth.hashers import check_password

from .models import Profile
from .models.home_content import HomeSection, DefaultShelfType, BookShelfSection
from .models.book import Book

User = get_user_model()


def validate_cpf(cpf):
    """
    Valida número de CPF brasileiro.

    Características:
    - Verifica quantidade de dígitos
    - Valida dígitos verificadores
    - Remove caracteres não numéricos

    Args:
        cpf (str): Número de CPF a ser validado

    Returns:
        str: CPF validado (somente números)

    Raises:
        forms.ValidationError: Se CPF for inválido
    """
    cpf = ''.join(filter(str.isdigit, cpf))

    if len(cpf) != 11:
        raise forms.ValidationError('CPF deve conter 11 dígitos.')

    if cpf == cpf[0] * 11:
        raise forms.ValidationError('CPF inválido.')

    # Validação dos dígitos verificadores
    for i in range(9, 11):
        value = sum((int(cpf[num]) * ((i + 1) - num) for num in range(0, i)))
        digit = ((value * 10) % 11) % 10
        if digit != int(cpf[i]):
            raise forms.ValidationError('CPF inválido.')
    return cpf


class UserRegistrationForm(UserCreationForm):
    """
    Formulário de registro de novo usuário.

    Características:
    - Campos personalizados além do UserCreationForm padrão
    - Validações extensivas para:
      * CPF
      * Email
      * Telefone
      * Data de nascimento
      * Senha
    """
    # Campos do formulário com validações e widgets personalizados
    cpf = forms.CharField(
        max_length=14,
        required=True,
        validators=[MinLengthValidator(11)],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    data_nascimento = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    telefone = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000'})
    )
    foto = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        """Metadados para configuração do formulário."""
        model = User
        fields = ('username', 'email', 'cpf', 'first_name', 'last_name',
                  'data_nascimento', 'telefone', 'foto', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_cpf(self):
        """
        Valida e verifica unicidade do CPF.

        Returns:
            str: CPF validado

        Raises:
            ValidationError: Se CPF já estiver cadastrado
        """
        cpf = self.cleaned_data.get('cpf')
        cpf = validate_cpf(cpf)
        if User.objects.filter(cpf=cpf).exists():
            raise forms.ValidationError('CPF já cadastrado.')
        return cpf

    def clean_email(self):
        """
        Valida unicidade do email.

        Returns:
            str: Email validado

        Raises:
            ValidationError: Se email já estiver cadastrado
        """
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email já cadastrado.')
        return email

    def clean_telefone(self):
        """
        Valida formato do telefone.

        Returns:
            str: Telefone com apenas números

        Raises:
            ValidationError: Se telefone for inválido
        """
        telefone = self.cleaned_data.get('telefone')
        telefone = ''.join(filter(str.isdigit, telefone))
        if len(telefone) < 10 or len(telefone) > 11:
            raise forms.ValidationError('Telefone inválido. Use o formato (00) 00000-0000')
        return telefone

    def clean_data_nascimento(self):
        """
        Valida idade do usuário.

        Returns:
            date: Data de nascimento

        Raises:
            ValidationError: Se usuário for menor de 18 anos
        """
        data_nascimento = self.cleaned_data.get('data_nascimento')
        if data_nascimento:
            hoje = date.today()
            idade = hoje.year - data_nascimento.year - (
                    (hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day))
            if idade < 18:
                raise forms.ValidationError('É necessário ter mais de 18 anos para se cadastrar.')
        return data_nascimento

    def clean_password2(self):
        """
        Valida senha com múltiplos critérios.

        Critérios:
        - Confirmação de senhas
        - Comprimento mínimo
        - Presença de maiúsculas
        - Presença de minúsculas
        - Presença de números
        - Presença de caracteres especiais

        Returns:
            str: Senha confirmada

        Raises:
            ValidationError: Se senha não atender aos critérios
        """
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('As senhas não conferem.')

        # Validações adicionais de senha
        if len(password1) < 8:
            raise forms.ValidationError('A senha deve ter pelo menos 8 caracteres.')
        if not re.search(r'[A-Z]', password1):
            raise forms.ValidationError('A senha deve conter pelo menos uma letra maiúscula.')
        if not re.search(r'[a-z]', password1):
            raise forms.ValidationError('A senha deve conter pelo menos uma letra minúscula.')
        if not re.search(r'[0-9]', password1):
            raise forms.ValidationError('A senha deve conter pelo menos um número.')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password1):
            raise forms.ValidationError('A senha deve conter pelo menos um caractere especial.')

        return password2


class UserProfileForm(forms.ModelForm):
    """
    Formulário para atualização de perfil de usuário.

    Características:
    - Campos adicionais para nome e email do usuário
    - Atualiza informações do usuário e do perfil
    """
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()

    class Meta:
        """Metadados para configuração do formulário de perfil."""
        model = Profile
        fields = ['bio', 'location', 'birth_date', 'interests']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'bio': forms.Textarea(attrs={'rows': 4}),
            'interests': forms.Textarea(attrs={'rows': 3})
        }

    def __init__(self, *args, **kwargs):
        """
        Inicializa o formulário com dados do usuário.

        Preenche campos de nome e email com dados do usuário associado.
        """
        super().__init__(*args, **kwargs)
        if self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):
        """
        Salva informações de perfil e usuário.

        Args:
            commit (bool): Se deve salvar imediatamente no banco de dados

        Returns:
            Profile: Objeto de perfil salvo
        """
        profile = super().save(commit=False)
        if commit:
            user = profile.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.save()
            profile.save()
        return profile


class ContatoForm(forms.Form):
    """
    Formulário de contato para comunicação com o site.

    Campos:
    - Nome
    - Email
    - Assunto
    - Mensagem

    Validação de email obrigatório
    """
    nome = forms.CharField(max_length=100)
    email = forms.EmailField()
    assunto = forms.CharField(max_length=200)
    mensagem = forms.CharField(widget=forms.Textarea)

    def clean_email(self):
        """
        Valida campo de email.

        Returns:
            str: Email validado

        Raises:
            ValidationError: Se email estiver vazio
        """
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError('Email é obrigatório.')
        return email


class CustomPasswordResetForm(PasswordResetForm):
    """
    Formulário customizado para reset de senha.
    """
    email = forms.EmailField(
        label='Email',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite seu email'
        })
    )

    def clean_email(self):
        """Valida se o email existe no sistema"""
        email = self.cleaned_data['email'].lower().strip()

        # Verifica se existe usuário com este email
        if not User.objects.filter(email=email).exists():
            print(f"❌ Email não cadastrado: {email}")
            raise forms.ValidationError("Este email não está cadastrado no sistema.")

        user = User.objects.get(email=email)

        # Verifica se o usuário está ativo
        if not user.is_active:
            print(f"❌ Usuário inativo: {email}")
            raise forms.ValidationError(
                "Esta conta está inativa. Entre em contato com o suporte."
            )

        return email

    def send_mail(
            self,
            subject_template_name,
            email_template_name,
            context,
            from_email,
            to_email,
            html_email_template_name=None,
    ):
        """Método personalizado para envio de email"""
        print("\n=== Enviando e-mail de reset de senha ===")
        print(f"Para: {to_email}")
        print(f"De: {settings.DEFAULT_FROM_EMAIL}")
        print(f"Backend: {settings.EMAIL_BACKEND}")
        print(f"Host: {settings.EMAIL_HOST}")

        try:
            # Renderiza o assunto
            subject = loader.render_to_string(subject_template_name, context)
            subject = "".join(subject.splitlines())

            # Renderiza o corpo do e-mail
            body = loader.render_to_string(email_template_name, context)

            # Envia o e-mail usando as configurações do settings.py
            result = send_mail(
                subject=subject,
                message=strip_tags(body),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                fail_silently=False,
                html_message=body,
            )

            if result:
                print("✅ E-mail enviado com sucesso!")
                return True

            print("❌ Falha no envio do email")
            return False

        except Exception as e:
            print(f"\n❌ Erro ao enviar e-mail: {str(e)}")
            print(f"Configurações atuais:")
            print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
            print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
            print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
            print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
            print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
            print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
            raise


class QuickShelfCreationForm(forms.Form):
    nome = forms.CharField(
        label='Nome da Prateleira',
        max_length=200,
        help_text='Este será o título exibido na página inicial',
        widget=forms.TextInput(attrs={'id': 'id_nome'})
    )

    identificador = forms.SlugField(
        label='Identificador',
        help_text='Identificador único usado para filtragem (somente letras, números e underscore)',
        required=False,
        widget=forms.TextInput(attrs={'id': 'id_identificador'})
    )

    filtro_campo = forms.ChoiceField(
        label='Campo do Filtro',
        choices=[
            ('tipo_shelf_especial', 'Tipo de Prateleira Especial'),
            ('e_lancamento', 'É Lançamento'),
            ('e_destaque', 'É Destaque'),
            ('adaptado_filme', 'Adaptado para Filme/Série'),
            ('e_manga', 'É Mangá'),
            ('quantidade_vendida', 'Quantidade Vendida'),
        ],
        initial='tipo_shelf_especial',
        help_text='Campo usado para filtrar os livros',
        widget=forms.Select(attrs={'id': 'id_filtro_campo'})
    )

    filtro_valor = forms.CharField(
        label='Valor do Filtro',
        max_length=100,
        required=False,
        help_text='Valor usado para filtrar (necessário apenas para alguns tipos de filtro)',
        widget=forms.TextInput(attrs={'id': 'id_filtro_valor'})
    )

    ordem = forms.IntegerField(
        label='Ordem de Exibição',
        initial=0,
        help_text='Ordem em que a prateleira aparecerá na página inicial',
        widget=forms.NumberInput(attrs={'id': 'id_ordem'})
    )

    max_livros = forms.IntegerField(
        label='Máximo de Livros',
        initial=12,
        min_value=1,
        max_value=50,
        help_text='Número máximo de livros exibidos nesta prateleira',
        widget=forms.NumberInput(attrs={'id': 'id_max_livros'})
    )

    ativo = forms.BooleanField(
        label='Ativo',
        initial=True,
        required=False,
        help_text='Indica se a prateleira está ativa e visível na página inicial',
        widget=forms.CheckboxInput(attrs={'id': 'id_ativo'})
    )

    def clean(self):
        cleaned_data = super().clean()
        filtro_campo = cleaned_data.get('filtro_campo')
        filtro_valor = cleaned_data.get('filtro_valor')
        identificador = cleaned_data.get('identificador')
        nome = cleaned_data.get('nome')

        # Se o identificador não foi fornecido, cria um a partir do nome
        if not identificador and nome:
            cleaned_data['identificador'] = slugify(nome).replace('-', '_')

        # Se o campo de filtro é 'tipo_shelf_especial' e não foi fornecido valor,
        # usa o identificador como valor padrão
        if filtro_campo == 'tipo_shelf_especial' and not filtro_valor:
            cleaned_data['filtro_valor'] = cleaned_data['identificador']

        # Para filtros booleanos, define o valor como 'True' se não especificado
        if filtro_campo in ['e_lancamento', 'e_destaque', 'adaptado_filme', 'e_manga'] and not filtro_valor:
            cleaned_data['filtro_valor'] = 'True'

        # Para quantidade_vendida, define como 0 se não especificado
        if filtro_campo == 'quantidade_vendida' and not filtro_valor:
            cleaned_data['filtro_valor'] = '0'

        # Verifica se o identificador já existe
        if DefaultShelfType.objects.filter(identificador=cleaned_data['identificador']).exists():
            raise ValidationError(
                f"Já existe um tipo de prateleira com o identificador '{cleaned_data['identificador']}'")

        return cleaned_data

    def save(self):
        """Cria todos os objetos necessários para uma prateleira completa"""
        nome = self.cleaned_data['nome']
        identificador = self.cleaned_data['identificador']
        filtro_campo = self.cleaned_data['filtro_campo']
        filtro_valor = self.cleaned_data['filtro_valor']
        ordem = self.cleaned_data['ordem']
        max_livros = self.cleaned_data['max_livros']
        ativo = self.cleaned_data['ativo']

        # 1. Cria o tipo de prateleira
        shelf_type = DefaultShelfType.objects.create(
            nome=nome,
            identificador=identificador,
            filtro_campo=filtro_campo,
            filtro_valor=filtro_valor,
            ordem=ordem,
            ativo=ativo
        )

        # 2. Cria a seção na home
        section = HomeSection.objects.create(
            titulo=nome,
            tipo='shelf',
            ordem=ordem,
            ativo=ativo
        )

        # 3. Cria a prateleira e associa com a seção e o tipo
        book_shelf = BookShelfSection.objects.create(
            section=section,
            shelf_type=shelf_type,
            max_livros=max_livros
        )

        return {
            'shelf_type': shelf_type,
            'section': section,
            'book_shelf': book_shelf
        }


# Adicionar após os outros formulários existentes
class BookForm(forms.ModelForm):
    """Formulário para edição de livros"""

    class Meta:
        model = Book
        fields = [
            'titulo', 'subtitulo', 'autor', 'tradutor', 'ilustrador',
            'editora', 'isbn', 'edicao', 'data_publicacao', 'numero_paginas',
            'idioma', 'formato', 'dimensoes', 'peso', 'categoria', 'genero',
            'descricao', 'temas', 'personagens', 'enredo', 'publico_alvo',
            'premios', 'adaptacoes', 'colecao', 'classificacao', 'citacoes',
            'curiosidades', 'website', 'capa', 'preco', 'preco_promocional'
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'subtitulo': forms.TextInput(attrs={'class': 'form-control'}),
            'autor': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'tradutor': forms.TextInput(attrs={'class': 'form-control'}),
            'ilustrador': forms.TextInput(attrs={'class': 'form-control'}),
            'editora': forms.TextInput(attrs={'class': 'form-control'}),
            'isbn': forms.TextInput(attrs={'class': 'form-control'}),
            'edicao': forms.TextInput(attrs={'class': 'form-control'}),
            'data_publicacao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'numero_paginas': forms.NumberInput(attrs={'class': 'form-control'}),
            'idioma': forms.TextInput(attrs={'class': 'form-control'}),
            'formato': forms.TextInput(attrs={'class': 'form-control'}),
            'dimensoes': forms.TextInput(attrs={'class': 'form-control'}),
            'peso': forms.TextInput(attrs={'class': 'form-control'}),
            'categoria': forms.TextInput(attrs={'class': 'form-control'}),
            'genero': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'temas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'personagens': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'enredo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'publico_alvo': forms.TextInput(attrs={'class': 'form-control'}),
            'premios': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'adaptacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'colecao': forms.TextInput(attrs={'class': 'form-control'}),
            'classificacao': forms.TextInput(attrs={'class': 'form-control'}),
            'citacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'curiosidades': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'capa': forms.FileInput(attrs={'class': 'form-control'}),
            'preco': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'preco_promocional': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Campos obrigatórios
        self.fields['titulo'].required = True
        self.fields['autor'].required = True

        # Configurações específicas
        if 'data_publicacao' in self.fields:
            self.fields['data_publicacao'].widget.format = '%Y-%m-%d'
            self.fields['data_publicacao'].input_formats = ['%Y-%m-%d']
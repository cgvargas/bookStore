# apps/core/forms.py
"""
Módulo de formulários para a aplicação CG BookStore.

Contém formulários para:
- Registro de usuário
- Atualização de perfil
- Formulário de contato

Inclui validações personalizadas para campos como CPF, email,
data de nascimento e senha.
"""

import re
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import MinLengthValidator
from datetime import date
from .models import Profile

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
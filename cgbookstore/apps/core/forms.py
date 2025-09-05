# Arquivo: cgbookstore/apps/core/forms.py
# VERSÃO COMPLETA E ATUALIZADA

import re
from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator
from datetime import date
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django.core.mail import send_mail
from django.template import loader
from django.utils.html import strip_tags
from django.conf import settings

from .models import Profile
from .models.book import Book

User = get_user_model()


def validate_cpf(cpf):
    cpf = ''.join(filter(str.isdigit, cpf))
    if len(cpf) != 11:
        raise forms.ValidationError('CPF deve conter 11 dígitos.')
    if cpf == cpf[0] * 11:
        raise forms.ValidationError('CPF inválido.')
    for i in range(9, 11):
        value = sum((int(cpf[num]) * ((i + 1) - num) for num in range(0, i)))
        digit = ((value * 10) % 11) % 10
        if digit != int(cpf[i]):
            raise forms.ValidationError('CPF inválido.')
    return cpf


class UserRegistrationForm(UserCreationForm):
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
        model = User
        fields = ('username', 'email', 'cpf', 'first_name', 'last_name',
                  'data_nascimento', 'telefone', 'foto', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')
        cpf = validate_cpf(cpf)
        if User.objects.filter(cpf=cpf).exists():
            raise forms.ValidationError('CPF já cadastrado.')
        return cpf

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email já cadastrado.')
        return email

    def clean_telefone(self):
        telefone = ''.join(filter(str.isdigit, self.cleaned_data.get('telefone')))
        if len(telefone) < 10 or len(telefone) > 11:
            raise forms.ValidationError('Telefone inválido. Use o formato (00) 00000-0000')
        return telefone

    def clean_data_nascimento(self):
        data_nascimento = self.cleaned_data.get('data_nascimento')
        if data_nascimento:
            hoje = date.today()
            idade = hoje.year - data_nascimento.year - (
                    (hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day))
            if idade < 18:
                raise forms.ValidationError('É necessário ter mais de 18 anos para se cadastrar.')
        return data_nascimento

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('As senhas não conferem.')
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
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()

    class Meta:
        model = Profile
        fields = ['bio', 'location', 'birth_date', 'interests']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'bio': forms.Textarea(attrs={'rows': 4}),
            'interests': forms.Textarea(attrs={'rows': 3})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            profile.save()
        return profile


class ContatoForm(forms.Form):
    nome = forms.CharField(max_length=100)
    email = forms.EmailField()
    assunto = forms.CharField(max_length=200)
    mensagem = forms.CharField(widget=forms.Textarea)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError('Email é obrigatório.')
        return email


class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label='Email',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite seu email'
        })
    )

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este email não está cadastrado no sistema.")
        user = User.objects.get(email=email)
        if not user.is_active:
            raise forms.ValidationError("Esta conta está inativa. Entre em contato com o suporte.")
        return email

    def send_mail(self, subject_template_name, email_template_name, context, from_email, to_email, html_email_template_name=None):
        subject = loader.render_to_string(subject_template_name, context)
        subject = "".join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)
        send_mail(
            subject=subject,
            message=strip_tags(body),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            fail_silently=False,
            html_message=body,
        )


class BookForm(forms.ModelForm):
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
            'data_publicacao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'temas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'personagens': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'enredo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'premios': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'adaptacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'citacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'curiosidades': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'capa': forms.FileInput(attrs={'class': 'form-control'}),
            'preco': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'preco_promocional': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
        # Adicionar a classe 'form-control' para todos os outros campos de texto
        for field in fields:
            if isinstance(widgets.get(field), (forms.TextInput, forms.URLInput, forms.EmailInput)):
                 widgets[field].attrs.update({'class': 'form-control'})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['titulo'].required = True
        self.fields['autor'].required = True
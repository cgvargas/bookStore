# Modelo de usuário
from django.contrib.auth.models import AbstractUser
from django.db import models
from stdimage.models import StdImageField
from django.contrib.auth.hashers import make_password

class User(AbstractUser):
    cpf = models.CharField('CPF', max_length=11, unique=True)
    data_nascimento = models.DateField('Data de Nascimento', null=True, blank=True)
    telefone = models.CharField('Telefone', max_length=15, null=True, blank=True)
    foto = StdImageField('Foto', upload_to='users', variations={'thumbnail': {'width': 100, 'height': 100, 'crop': True}}, delete_orphans=True, null=True, blank=True)
    is_active = models.BooleanField('Ativo', default=True)
    is_staff = models.BooleanField('Staff', default=False)
    date_joined = models.DateTimeField('Data de Entrada', auto_now_add=True)
    modified = models.DateTimeField('Data de Modificação', auto_now=True)
    email_verified = models.BooleanField('Email Verificado', default=False)
    email_verification_token = models.CharField('Token de Verificação', max_length=100, null=True, blank=True)
    password_history = models.JSONField('Histórico de Senhas', default=list, blank=True)

    def save_password_to_history(self, password):
        """Salva a senha no histórico, mantendo apenas as 3 últimas"""
        hashed_password = make_password(password)
        history = self.password_history if self.password_history else []
        history.append(hashed_password)

        # Mantém apenas as 3 últimas senhas
        if len(history) > 3:
            history = history[-3:]

        self.password_history = history
        self.save(update_fields=['password_history'])

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        db_table = 'user'

    def __str__(self):
        return self.get_full_name() if self.get_full_name() else self.username
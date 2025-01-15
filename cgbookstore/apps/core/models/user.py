# Modelo de usuário
from django.contrib.auth.models import AbstractUser
from django.db import models
from stdimage.models import StdImageField

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

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        db_table = 'user'

    def __str__(self):
        return self.get_full_name() if self.get_full_name() else self.username
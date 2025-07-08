# cgbookstore/apps/core/recommendations/tests/test_helpers.py

import uuid
from django.contrib.auth import get_user_model

User = get_user_model()


def create_test_user(username, password='testpass123', **kwargs):
    """
    Helper para criar usuários de teste com CPF único
    """
    # Gera CPF único para testes
    cpf = kwargs.pop('cpf', f'{uuid.uuid4().hex[:11]}')

    return User.objects.create_user(
        username=username,
        password=password,
        cpf=cpf,
        **kwargs
    )
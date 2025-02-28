import os
import django
from django.conf import settings

# Configure o caminho do projeto
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cgbookstore.config.settings")
django.setup()

# Configurações adicionais para pytest
def pytest_configure(config):
    """
    Configurações globais para os testes
    """
    # Definir configurações de teste adicionais, se necessário
    settings.DEBUG = True
    settings.TESTING = True
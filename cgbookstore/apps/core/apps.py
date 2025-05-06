# cgbookstore/apps/core/apps.py
"""
Configuração do aplicativo core para o projeto CG BookStore.

Este módulo define a configuração do aplicativo Django,
incluindo configurações padrão e importação de sinais.
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """
    Configuração do aplicativo Core.

    Características:
    - Define campo de chave primária padrão
    - Configura nome do aplicativo
    - Importa sinais quando o aplicativo está pronto
    """
    # Tipo de campo de chave primária padrão para novos modelos
    default_auto_field = 'django.db.models.BigAutoField'

    # Caminho completo do aplicativo
    name = 'cgbookstore.apps.core'

    # Nome legível do aplicativo
    verbose_name = 'Organização'

    def ready(self):
        """
        Método chamado quando o aplicativo está pronto.

        Importa os sinais do aplicativo para registrar
        manipuladores de eventos e outras configurações iniciais.
        """
        # Importa os sinais definidos no módulo de sinais
        import cgbookstore.apps.core.signals
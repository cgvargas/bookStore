# cgbookstore/apps/core/admin.py
"""
Módulo de configuração do painel administrativo para o projeto CG BookStore.

Este arquivo agora serve apenas como um ponto de entrada, importando e expondo
o site administrativo customizado definido no pacote admin.
"""

# Importa apenas o site administrativo do módulo admin
from .admin import admin_site

# Exporta o site administrativo para uso no projeto
__all__ = ['admin_site']
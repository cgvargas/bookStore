"""
Módulo de compatibilidade para a transição para o serviço centralizado.
Redireciona para a implementação em google_books_service.py
"""
import logging
from cgbookstore.apps.core.services.google_books_service import GoogleBooksClient as CentralizedClient

logger = logging.getLogger(__name__)
logger.warning("ATENÇÃO: Usando versão de compatibilidade do GoogleBooksClient. Atualize suas importações para usar 'services.google_books_service'")

# Reexporta a classe centralizada para compatibilidade com código existente
GoogleBooksClient = CentralizedClient
"""
Arquivo de compatibilidade para transição para o novo serviço centralizado.
"""
import logging
from cgbookstore.apps.core.services.google_books_service import GoogleBooksCache as CentralizedCache

logger = logging.getLogger(__name__)
logger.warning("ATENÇÃO: Usando módulo de compatibilidade do GoogleBooksCache. Atualize suas importações para usar 'services.google_books_service'")

# Classe de compatibilidade que apenas repassa para a implementação centralizada
class GoogleBooksCache(CentralizedCache):
    """Wrapper de compatibilidade para a classe GoogleBooksCache centralizada"""
    pass
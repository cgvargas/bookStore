# cgbookstore/apps/chatbot_literario/services/__init__.py
import logging

logger = logging.getLogger(__name__)

# --- Ordem de Carregamento Controlada ---

# 1. Serviços que não dependem de outros
try:
    from .ai_service import ai_service, is_ai_available
    logger.info("✅ Serviço de IA (ai_service) carregado.")
except ImportError as e:
    logger.error(f"❌ Falha ao carregar ai_service: {e}")
    ai_service = None
    def is_ai_available(): return False

try:
    from .embeddings import EmbeddingsService
    embeddings_service = EmbeddingsService()
    logger.info("✅ Serviço de Embeddings (embeddings_service) carregado.")
except ImportError as e:
    logger.error(f"❌ Falha ao carregar embeddings_service: {e}")
    embeddings_service = None

# 2. Serviços que dependem dos anteriores
try:
    from .training_service import TrainingService
    training_service = TrainingService(
        ai_service=ai_service,
        embeddings_service=embeddings_service
    )
    logger.info("✅ Serviço de Treinamento (training_service) carregado.")
except ImportError as e:
    logger.error(f"❌ Falha ao carregar training_service: {e}")
    training_service = None

# 3. Serviço final que depende do training_service
try:
    from .functional_chatbot import FunctionalChatbot
    # ✅ CORREÇÃO: Cria a instância aqui, injetando a dependência de forma explícita.
    functional_chatbot = FunctionalChatbot(
        training_service=training_service
    )
    logger.info("✅ Serviço Funcional do Chatbot (functional_chatbot) carregado.")
except ImportError as e:
    logger.error(f"❌ Falha ao carregar functional_chatbot: {e}")
    functional_chatbot = None

# --- Exportação dos Símbolos ---
__all__ = [
    'ai_service',
    'is_ai_available',
    'embeddings_service',
    'training_service',
    'functional_chatbot',
]
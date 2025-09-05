# cgbookstore/apps/chatbot_literario/services/chatbot_types.py

from dataclasses import dataclass
from typing import Optional, Dict, Any, List


@dataclass
class SearchResult:
    """
    ✅ Resultado de busca semântica na base de conhecimento
    Usado pelo EmbeddingsService e TrainingService
    """
    answer: str
    source: str
    confidence: float
    question_found: str
    context_match: bool = True

    # Campos opcionais para compatibilidade
    category: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ChatbotResponse:
    """
    ✅ Resposta padronizada do chatbot
    Usado pelo FunctionalChatbot e AI Service
    """
    response: str
    success: bool = True
    source: str = 'ai'
    confidence: float = 1.0

    # Metadados opcionais
    response_time: Optional[float] = None
    model_used: Optional[str] = None
    token_count: Optional[int] = None
    knowledge_items_used: int = 0
    error: Optional[str] = None


# ✅ EXPORTS
__all__ = [
    'SearchResult',
    'ChatbotResponse'
]
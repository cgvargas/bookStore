# cgbookstore/apps/chatbot_literario/services/chatbot_types.py
"""
Arquivo para centralizar tipos de dados e estruturas compartilhadas
entre os diferentes serviços do chatbot para evitar dependências circulares.
"""
from typing import NamedTuple, Optional, List, Dict, Any

class SearchResult(NamedTuple):
    """
    Representa um resultado de busca, seja da base de conhecimento local ou da IA.
    """
    answer: str
    source: str
    confidence: float
    context_match: bool = False
    question_found: Optional[str] = None


class ChatContext(NamedTuple):
    """
    Representa o contexto completo da conversa para ser usado pela IA.
    """
    entities: Dict[str, List[str]]
    last_topic: Optional[str]
    last_question_type: Optional[str]
    conversation_history: Optional[List[Dict[str, Any]]]
    user_id: Optional[str]
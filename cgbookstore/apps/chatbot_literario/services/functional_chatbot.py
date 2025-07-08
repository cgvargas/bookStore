# cgbookstore/apps/chatbot_literario/services/functional_chatbot.py

import logging
import re
from typing import List, Any, Dict
from django.db.models import Q

logger = logging.getLogger(__name__)


class FunctionalChatbot:
    """
    Chatbot "stateless" que usa o banco de dados para manter o contexto.
    """

    def __init__(self, training_service: Any = None):
        self.training_service = training_service
        self.max_history_pairs = 5
        if not self.training_service:
            logger.warning("FunctionalChatbot inicializado sem um training_service.")

    # ✅ CORREÇÃO: Usar strings para os type hints para evitar o NameError na inicialização.
    def get_response(self, user_message: str, conversation: 'Conversation') -> Dict[str, Any]:
        logger.info(f"Processando mensagem para conversation_id '{conversation.id}': {user_message[:100]}...")
        history = self._load_history_from_db(conversation)
        relevant_knowledge = self._get_relevant_knowledge(user_message)
        messages_for_ai = self._build_chat_prompt(user_message, history, relevant_knowledge)

        from .ai_service import ai_service
        ai_response = ai_service.generate_response(messages_for_ai)

        return ai_response

    def _load_history_from_db(self, conversation: 'Conversation') -> List[Dict[str, str]]:
        # ✅ CORREÇÃO: Usar string no type hint
        max_messages = self.max_history_pairs * 2
        messages = conversation.messages.order_by('-timestamp')[:max_messages]
        history = []
        for msg in reversed(messages):
            role = "user" if msg.sender == 'user' else "assistant"
            history.append({"role": role, "content": msg.content})
        return history

    def _get_relevant_knowledge(self, message: str) -> List['KnowledgeItem']:
        """
        Busca conhecimento relevante de forma mais inteligente.
        """
        # ✅ CORREÇÃO: Importar o modelo DENTRO da função.
        from ..models import KnowledgeItem

        # 1. Extração de Entidades
        entities = re.findall(
            r'["\']([^"\']+)["\']|'  # Captura texto entre aspas
            r'\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)\b|'  # Captura nomes compostos (ex: Quarta Asa)
            r'\b([A-Z][a-z]{4,})\b',  # Captura palavras únicas com maiúscula e mais de 4 letras (evita pegar "Olá")
            message
        )
        extracted_terms = [term for group in entities for term in group if term]

        if extracted_terms:
            logger.info(f"Entidades extraídas da mensagem: {extracted_terms}")
            knowledge_items = set()
            for term in extracted_terms:
                items = KnowledgeItem.objects.filter(
                    Q(question__icontains=term) | Q(answer__icontains=term),
                    active=True
                )
                knowledge_items.update(items)

            if knowledge_items:
                logger.info(f"{len(knowledge_items)} fatos encontrados para as entidades.")
                return list(knowledge_items)

        # 3. Fallback para a busca semântica
        if not self.training_service:
            logger.warning("Busca semântica de fallback pulada: training_service não está disponível.")
            return []

        logger.info("Nenhuma entidade clara encontrada, usando busca semântica padrão.")
        try:
            return self.training_service.search_knowledge(query=message, limit=3) or []
        except Exception as e:
            logger.error(f"Erro na busca semântica de fallback: {e}", exc_info=True)
            return []

    def _build_chat_prompt(self, user_message: str, history: List[Dict], knowledge: List[Any]) -> List[Dict]:
        system_prompt = (
            "Você é o 'Chatbot Literário', um assistente especialista. Sua tarefa é usar o CONTEXTO fornecido para responder à pergunta do usuário.\n\n"
            "REGRAS OBRIGATÓRIAS:\n"
            "1. **ANALISE O CONTEXTO:** O contexto contém o 'Histórico da Conversa' e uma 'Base de Fatos' sobre entidades (livros, autores).\n"
            "2. **SINTETIZE A RESPOSTA:** Use TODOS os fatos relevantes da 'Base de Fatos' para construir uma resposta completa e coesa. Não responda apenas com um fato se houver vários disponíveis.\n"
            "3. **USE O HISTÓRICO:** Se a pergunta for uma continuação (ex: 'e sobre ele?'), use o histórico para identificar a entidade principal da conversa.\n"
            "4. **NÃO INVENTE:** Se a 'Base de Fatos' estiver vazia ou não contiver a informação solicitada, responda EXATAMENTE: 'Não tenho essa informação específica em minha base de dados.' Não sugira outros tópicos aleatoriamente."
        )

        messages = [{"role": "system", "content": system_prompt}]

        if knowledge:
            knowledge_text = "--- BASE DE FATOS ---\n"
            for item in knowledge:
                # ✅ CORREÇÃO: Lidar com ambos os tipos de objeto (KnowledgeItem e SearchResult)
                # Usamos getattr() para buscar o atributo de forma segura, com um fallback.

                # Para a pergunta/tópico
                question_text = getattr(item, 'question', None) or getattr(item, 'question_found', 'Tópico relacionado')

                # Para a resposta/fato
                answer_text = getattr(item, 'answer', 'Informação não disponível.')

                knowledge_text += f"- Fato sobre '{question_text}': {answer_text}\n"

            knowledge_text += "--- FIM DA BASE DE FATOS ---\n"
            messages.append({"role": "system", "content": knowledge_text})

        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": user_message})

        return messages